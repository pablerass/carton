import httpx2
import pytest
from fastapi.testclient import TestClient

import carton.api as carton_api
from carton.models.boardgame import BGGDesigner, BGGGame
from carton.models.params import Players, PlayTime
from carton.providers import BggGameNotFoundError, BggUserNotFoundError


@pytest.fixture(autouse=True)
def clean_bgg_environment(monkeypatch, tmp_path):
    for var in ("BGG_USER", "BGG_PASSWORD", "BGG_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CARTON_CACHE_FILE", str(tmp_path / "cache.pickle"))


class FakeProvider:
    def __init__(self):
        self.api_keys = []
        self.user_logins = []
        self.closed = False
        self.collection_result: list[BGGGame] | Exception = []
        self.games_result: list[BGGGame] | Exception = []
        self.requested_ids = []

    def api_login(self, api_key):
        self.api_keys.append(api_key)

    def user_login(self, user, password):
        self.user_logins.append((user, password))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        self.closed = True

    async def user_collection(self, user):
        if isinstance(self.collection_result, Exception):
            raise self.collection_result
        return self.collection_result

    async def boardgames_by_id(self, ids):
        self.requested_ids.append(list(ids))
        if isinstance(self.games_result, Exception):
            raise self.games_result
        return self.games_result


@pytest.fixture
def provider(monkeypatch):
    fake = FakeProvider()
    monkeypatch.setattr(carton_api, "BggProvider", lambda **kwargs: fake)
    return fake


@pytest.fixture
def client(monkeypatch, provider):
    monkeypatch.setenv("BGG_API_KEY", "key")
    with TestClient(carton_api.app) as client:
        yield client


def test_startup_logs_in_with_api_key(client, provider):
    assert provider.api_keys == ["key"]
    assert provider.user_logins == []


def test_startup_logs_in_with_password(monkeypatch, provider):
    monkeypatch.setenv("BGG_USER", "alice")
    monkeypatch.setenv("BGG_PASSWORD", "secret")

    with TestClient(carton_api.app):
        assert provider.user_logins == [("alice", "secret")]
    assert provider.closed


@pytest.mark.parametrize('environment', [
    {},
    {"BGG_PASSWORD": "secret"},
    {"BGG_API_KEY": "key", "BGG_USER": "alice", "BGG_PASSWORD": "secret"},
])
def test_startup_requires_valid_authentication(monkeypatch, provider, environment):
    for var, value in environment.items():
        monkeypatch.setenv(var, value)

    with pytest.raises(RuntimeError), TestClient(carton_api.app):
        pass


def test_user_collection(client, provider):
    provider.collection_result = [
        BGGGame(name="Catan", bgg_id=13, designers={BGGDesigner(name="Klaus Teuber", bgg_id=11)},
                players=Players.from_values([3, 4]), play_time=PlayTime(lower=60, upper=120),
                rating=7.1, rank=500),
    ]

    response = client.get("/users/alice/collection")

    assert response.status_code == 200
    [game] = response.json()
    assert game["name"] == "Catan"
    assert game["bgg_id"] == 13
    assert game["designers"] == [{"name": "Klaus Teuber", "bgg_id": 11}]
    assert game["players"] == {"intervals": [{"lower": 3, "upper": 4}]}
    assert game["play_time"] == {"lower": 60, "upper": 120}
    assert game["rank"] == 500


@pytest.mark.parametrize('error, status_code', [
    (BggUserNotFoundError("alice"), 404),
    (TimeoutError(), 504),
    (httpx2.ConnectError("unreachable"), 502),
])
def test_user_collection_errors(client, provider, error, status_code):
    provider.collection_result = error

    response = client.get("/users/alice/collection")

    assert response.status_code == status_code


def _recommendation_games() -> list[BGGGame]:
    return [
        BGGGame(name="Catan", bgg_id=13, players=Players.from_values([3, 4]),
                play_time=PlayTime(lower=60, upper=120), community_average_weight=2.3, geek_rating=7.0),
        BGGGame(name="Azul", bgg_id=230802, players=Players.from_values([2, 3, 4]),
                play_time=PlayTime(lower=30, upper=45), community_average_weight=1.8, geek_rating=7.6),
        BGGGame(name="Twilight Imperium", bgg_id=233078, players=Players.from_values([3, 4, 5, 6]),
                play_time=PlayTime(lower=240, upper=480), community_average_weight=4.3, geek_rating=8.4),
    ]


def test_recommend(client, provider):
    provider.games_result = _recommendation_games()

    response = client.post("/recommend", json={"players": 3, "time": 90, "complexity": 2,
                                               "games": [13, 230802, 233078]})

    assert response.status_code == 200
    assert provider.requested_ids == [[13, 230802, 233078]]
    recommendations = response.json()
    assert [r["game"]["name"] for r in recommendations] == ["Azul", "Catan"]
    assert recommendations[0]["score"] >= recommendations[1]["score"]
    assert set(recommendations[0]) == {"game", "score", "players_score", "time_score",
                                       "complexity_score", "rating_score"}


def test_recommend_limit(client, provider):
    provider.games_result = _recommendation_games()

    response = client.post("/recommend", json={"players": 3, "time": 600, "games": [13, 230802, 233078],
                                               "limit": 1})

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.parametrize('body', [
    {"players": 3, "time": 90},
    {"players": 3, "time": 90, "games": []},
    {"players": 0, "time": 90, "games": [13]},
    {"players": 3, "time": 90, "complexity": 6, "games": [13]},
])
def test_recommend_invalid_request(client, provider, body):
    response = client.post("/recommend", json=body)

    assert response.status_code == 422
    assert provider.requested_ids == []


@pytest.mark.parametrize('error, status_code', [
    (BggGameNotFoundError([1]), 404),
    (TimeoutError(), 504),
    (httpx2.ConnectError("unreachable"), 502),
])
def test_recommend_errors(client, provider, error, status_code):
    provider.games_result = error

    response = client.post("/recommend", json={"players": 3, "time": 90, "games": [1]})

    assert response.status_code == status_code
