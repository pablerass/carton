import sys

import pandas as pd

import carton.__main__ as carton_main


def test_parse_args_uses_environment(monkeypatch):
    monkeypatch.setenv("BGG_USER", "alice")
    monkeypatch.setenv("BGG_PASSWORD", "secret")
    monkeypatch.setenv("BGG_API_KEY", "key")

    args = carton_main.parse_args([])

    assert args.bgg_user == "alice"
    assert args.bgg_password == "secret"
    assert args.bgg_api_key == "key"
    assert args.verbose == 0


def test_main_logs_in_and_exports_games(monkeypatch):
    exported = {}
    api_keys = []

    class FakeProvider:
        def api_login(self, api_key):
            api_keys.append(api_key)

        def user_collection(self, user):
            assert user == "alice"
            return [{"bgg_id": 1, "designers": ["Designer"]}]

    monkeypatch.setattr(carton_main, "BggProvider", FakeProvider)
    monkeypatch.setattr(carton_main.asyncio, "run", lambda collection: collection)
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
    assert exported == {"path": "~/file.csv", "index": False}
