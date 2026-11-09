import csv
import io
import json

import pytest

import carton.__main__ as carton_main
from carton.models.boardgame import BGGDesigner, BGGGame
from carton.models.params import Players, PlayTime
from carton.providers import BggGameNotFoundError, BggUserNotFoundError


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
        self.requested_ids = []
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

    async def boardgames_by_id(self, ids):
        self.requested_ids.append(list(ids))
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


# recommend

RECOMMEND_ARGS = ["--players", "3", "--time", "120", "--bgg-api-key", "key"]


def test_parse_args_recommend(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")

    args = carton_main.parse_args(["recommend", *RECOMMEND_ARGS])

    assert args.user == "alice"
    assert args.games_file is None
    assert (args.players, args.time, args.complexity, args.limit) == (3, 120, None, 10)


def test_parse_args_recommend_games_file_does_not_use_bgg_user(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")

    args = carton_main.parse_args(["recommend", "--games-file", "games.txt", *RECOMMEND_ARGS])

    assert args.user is None
    assert args.games_file == "games.txt"


@pytest.mark.parametrize('args', [
    ["recommend", *RECOMMEND_ARGS],  # No user nor games file
    ["recommend", "bob", "--games-file", "games.txt", *RECOMMEND_ARGS],  # Both user and games file
    ["recommend", "bob", "--time", "120", "--bgg-api-key", "key"],  # No players
    ["recommend", "bob", "--players", "3", "--bgg-api-key", "key"],  # No time
    ["recommend", "bob", *RECOMMEND_ARGS, "--complexity", "6"],
    ["recommend", "bob", *RECOMMEND_ARGS, "--players", "0"],
    ["recommend", "bob", *RECOMMEND_ARGS, "--limit", "0"],
    ["recommend", "bob", "--players", "3", "--time", "120"],  # No authentication
])
def test_parse_args_recommend_invalid(args):
    with pytest.raises(SystemExit):
        carton_main.parse_args(args)


@pytest.mark.parametrize('content', [
    "13\n\n# A comment\n230802\n",
    "name,bgg_id,players\nCatan,13,3-4\nAzul,230802,\"2, 3\"\n",
    "[13, 230802]",
    '[{"name": "Catan", "bgg_id": 13}, {"name": "Azul", "bgg_id": 230802}]',
])
def test_read_game_ids(content):
    assert carton_main.read_game_ids(io.StringIO(content)) == [13, 230802]


def test_main_recommend_user_collection(fake_provider, capsys):
    assert carton_main.main(["recommend", "alice", *RECOMMEND_ARGS]) == 0
    assert fake_provider.users == ["alice"]
    assert fake_provider.closed == [True]

    [row] = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))
    assert row["name"] == "Catan"
    assert row["bgg_id"] == "13"
    assert 0 < float(row["score"]) <= 1


def test_main_recommend_games_file(fake_provider, tmp_path):
    games_file = tmp_path / "games.txt"
    games_file.write_text("13\n13\n")
    output = tmp_path / "recommendations.json"

    assert carton_main.main(["recommend", "--games-file", str(games_file), *RECOMMEND_ARGS,
                             "--format", "json", "--output", str(output)]) == 0
    assert fake_provider.requested_ids == [[13, 13]]

    [recommendation] = json.loads(output.read_text())
    assert recommendation["game"]["name"] == "Catan"


def test_main_recommend_games_not_playable(fake_provider, capsys):
    # Catan is for 3-4 players
    assert carton_main.main(["recommend", "alice", *RECOMMEND_ARGS, "--players", "2"]) == 0

    assert list(csv.DictReader(io.StringIO(capsys.readouterr().out))) == []


@pytest.mark.parametrize('content', ["", "not an id\n"])
def test_main_recommend_invalid_games_file(fake_provider, tmp_path, content):
    games_file = tmp_path / "games.txt"
    games_file.write_text(content)

    assert carton_main.main(["recommend", "--games-file", str(games_file), *RECOMMEND_ARGS]) == 1
    assert fake_provider.requested_ids == []


def test_main_recommend_missing_games_file(fake_provider, tmp_path):
    assert carton_main.main(["recommend", "--games-file", str(tmp_path / "missing.txt"), *RECOMMEND_ARGS]) == 1


@pytest.mark.parametrize('error', [BggUserNotFoundError("alice"), BggGameNotFoundError([13])])
def test_main_recommend_not_found(fake_provider, capsys, error):
    fake_provider.error = error

    assert carton_main.main(["recommend", "alice", *RECOMMEND_ARGS]) == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize('output_format', carton_main.OUTPUT_FORMATS)
def test_read_game_ids_from_collection_output(output_format):
    # 'recommend' reads the files written by 'collection' in every output format
    games = [*_games(), BGGGame(name="Azul", bgg_id=230802, designers={BGGDesigner(name="Michael Kiesling", bgg_id=7),
                                                                       BGGDesigner(name="Other, Designer", bgg_id=8)})]
    output = io.StringIO()
    carton_main.write_collection(games, output, output_format)
    output.seek(0)

    assert carton_main.read_game_ids(output) == [13, 230802]
