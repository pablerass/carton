import csv
import io
import json

import pytest

import carton.__main__ as carton_main
from carton.models.boardgame import BGGDesigner, BGGGame
from carton.models.params import Players, PlayTime
from carton.providers import BggUserNotFoundError


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch, tmp_path):
    for var in ("BGG_USER", "BGG_PASSWORD", "BGG_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CARTON_CACHE_FILE", str(tmp_path / "cache.pickle"))


def _games() -> list[BGGGame]:
    return [
        BGGGame(name="Catan", bgg_id=13,
                designers={BGGDesigner(name="Klaus Teuber", bgg_id=11)},
                players=Players.from_values([3, 4]), play_time=PlayTime(lower=60, upper=120),
                rating=7.1),
    ]


def test_parse_args_requires_command():
    with pytest.raises(SystemExit):
        carton_main.parse_args([])


# collection

def test_parse_args_collection_uses_environment(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")
    monkeypatch.setenv("BGG_API_KEY", "key")

    args = carton_main.parse_args(["collection"])

    assert args.user == "alice"
    assert args.bgg_password is None
    assert args.bgg_api_key == "key"
    assert args.format == "csv"
    assert args.output == "-"


def test_parse_args_collection_user_argument(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")
    monkeypatch.setenv("BGG_API_KEY", "key")

    assert carton_main.parse_args(["collection", "bob"]).user == "bob"


@pytest.mark.parametrize('environment, args', [
    ({"BGG_API_KEY": "key"}, ["collection"]),  # No user
    ({"BGG_USER": "alice"}, ["collection"]),  # No authentication
    ({"BGG_PASSWORD": "secret"}, ["collection", "bob"]),  # Password without a user to log in
    ({"BGG_USER": "alice", "BGG_PASSWORD": "secret", "BGG_API_KEY": "key"}, ["collection"]),  # Both methods
])
def test_parse_args_collection_invalid(monkeypatch, environment, args):
    for var, value in environment.items():
        monkeypatch.setenv(var, value)

    with pytest.raises(SystemExit):
        carton_main.parse_args(args)


class FakeProvider:
    def __init__(self):
        self.api_keys = []
        self.users = []
        self.closed = []
        self.error: Exception | None = None

    def api_login(self, api_key):
        self.api_keys.append(api_key)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        self.closed.append(True)

    async def user_collection(self, user):
        self.users.append(user)
        if self.error:
            raise self.error
        return _games()


@pytest.fixture
def fake_provider(monkeypatch):
    fake = FakeProvider()
    monkeypatch.setattr(carton_main, "BggProvider", lambda **kwargs: fake)
    return fake


def test_main_collection_writes_csv(fake_provider, capsys):
    assert carton_main.main(["collection", "alice", "--bgg-api-key", "key"]) == 0
    assert fake_provider.api_keys == ["key"]
    assert fake_provider.users == ["alice"]
    assert fake_provider.closed == [True]

    [row] = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))
    assert row["name"] == "Catan"
    assert row["bgg_id"] == "13"
    assert row["designers"] == "Klaus Teuber"
    assert row["players"] == "3-4"
    assert row["play_time"] == "60-120"
    assert row["min_age"] == ""


def test_main_collection_writes_json_file(fake_provider, tmp_path):
    output = tmp_path / "collection.json"

    assert carton_main.main(["collection", "alice", "--bgg-api-key", "key",
                             "--format", "json", "--output", str(output)]) == 0

    [game] = json.loads(output.read_text())
    assert game["name"] == "Catan"
    assert game["designers"] == [{"name": "Klaus Teuber", "bgg_id": 11}]


def test_main_collection_unknown_user(fake_provider, capsys):
    fake_provider.error = BggUserNotFoundError("alice")

    assert carton_main.main(["collection", "alice", "--bgg-api-key", "key"]) == 1
    assert capsys.readouterr().out == ""
