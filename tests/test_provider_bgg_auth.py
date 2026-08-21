import pytest
from httpx import HTTPStatusError

from carton.providers.bgg_provider import BggProvider, BGG_LOGIN_URL


@pytest.fixture(autouse=True)
def disable_proxy_environment(monkeypatch):
    for variable in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                     "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(variable, raising=False)


async def test_user_login_stores_cookies_and_reuses_them(httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=BGG_LOGIN_URL,
        status_code=200,
        headers={"set-cookie": "sessionid=abc; Path=/; HttpOnly"},
    )

    bgg = BggProvider()
    bgg.user_login("alice", "secret")

    httpx_mock.add_response(
        method='GET',
        url=f"{bgg._api.xml2}/search?query=whatever&type=boardgame&exact=1",
        status_code=200,
        text="<items total=\"0\"></items>",
    )

    assert await bgg.boardgame_by_name("whatever") is None

    reqs = httpx_mock.get_requests()
    get_reqs = [r for r in reqs if r.method == "GET"]
    assert get_reqs, "No GET requests were recorded"
    last_get = get_reqs[-1]
    assert last_get.headers.get("cookie") == "sessionid=abc"
    assert dict(last_get.url.params) == {
        "query": "whatever",
        "type": "boardgame",
        "exact": "1",
    }


async def test_api_login_and_logout_control_request_authentication(httpx_mock):
    bgg = BggProvider(api_key="token")

    httpx_mock.add_response(
        method="GET",
        url=f"{bgg._api.xml2}/search?query=whatever&type=boardgame&exact=1",
        status_code=200,
        text="<items total=\"0\"></items>",
    )
    assert await bgg.boardgame_by_name("whatever") is None
    assert httpx_mock.get_requests()[-1].headers["authorization"] == "Bearer token"

    bgg.logout()
    httpx_mock.add_response(
        method="GET",
        url=f"{bgg._api.xml2}/search?query=whatever&type=boardgame&exact=1",
        status_code=200,
        text="<items total=\"0\"></items>",
    )
    assert await bgg.boardgame_by_name("whatever") is None
    assert "authorization" not in httpx_mock.get_requests()[-1].headers


def test_user_login_accepts_successful_http_response(httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=BGG_LOGIN_URL,
        status_code=200,
        json={"success": False, "error": "invalid credentials"},
    )

    bgg = BggProvider()
    bgg.user_login("bob", "wrong")

    request = httpx_mock.get_requests()[0]
    assert request.content == b'{"credentials":{"username":"bob","password":"wrong"}}'


def test_authenticate_http_error_raises(httpx_mock):
    # Server returns an HTTP error status
    httpx_mock.add_response(
        method='POST',
        url=BGG_LOGIN_URL,
        status_code=401,
        text="Unauthorized",
    )

    bgg = BggProvider()
    with pytest.raises(HTTPStatusError):
        bgg.user_login("eve", "bad")
