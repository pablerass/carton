import httpx
import pytest
from fastapi.testclient import TestClient

import carton.api as carton_api
from carton.models.boardgame import BGGDesigner, BGGGame
from carton.models.params import Players, PlayTime
from carton.providers import BggUserNotFoundError


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
    (httpx.ConnectError("unreachable"), 502),
])
def test_user_collection_errors(client, provider, error, status_code):
    provider.collection_result = error

    response = client.get("/users/alice/collection")

    assert response.status_code == status_code
