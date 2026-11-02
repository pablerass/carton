import sys

import pandas as pd
import pytest

import carton.__main__ as carton_main


@pytest.fixture(autouse=True)
def clean_bgg_environment(monkeypatch):
    for var in ("BGG_USER", "BGG_PASSWORD", "BGG_API_KEY"):
        monkeypatch.delenv(var, raising=False)


def test_parse_args_uses_environment(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")
    monkeypatch.setenv("BGG_API_KEY", "key")

    args = carton_main.parse_args([])

    assert args.bgg_user == "alice"
    assert args.bgg_password is None
    assert args.bgg_api_key == "key"
    assert args.verbose == 0


def test_parse_args_requires_user(monkeypatch):
    monkeypatch.setenv("BGG_API_KEY", "key")

    with pytest.raises(SystemExit):
        carton_main.parse_args([])


def test_parse_args_requires_authentication(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")

    with pytest.raises(SystemExit):
        carton_main.parse_args([])


def test_parse_args_rejects_both_authentication_methods(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")
    monkeypatch.setenv("BGG_PASSWORD", "secret")
    monkeypatch.setenv("BGG_API_KEY", "key")

    with pytest.raises(SystemExit):
        carton_main.parse_args([])


def test_main_logs_in_and_exports_games(monkeypatch):
    exported = {}
    api_keys = []
    closed = []

    class FakeProvider:
        def api_login(self, api_key):
            api_keys.append(api_key)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            closed.append(True)

        async def user_collection(self, user):
            assert user == "alice"
            return [{"bgg_id": 1, "designers": ["Designer"]}]

    monkeypatch.setattr(carton_main, "BggProvider", FakeProvider)
    monkeypatch.setattr(
        pd.DataFrame,
        "to_csv",
        lambda frame, path, index=False: exported.update(path=path, index=index),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["carton", "--bgg-user", "alice", "--bgg-api-key", "key"],
    )

    assert carton_main.main() == 0
    assert api_keys == ["key"]
    assert closed == [True]
    assert exported == {"path": "~/file.csv", "index": False}
