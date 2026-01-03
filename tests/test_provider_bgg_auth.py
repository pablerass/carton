import pytest
from httpx import HTTPStatusError

from carton.providers.bgg_provider import BggProvider, BGG_LOGIN_URL


def test_authenticate_stores_cookies(httpx_mock):
    # Mock the login response to set a cookie and return a success JSON body
    httpx_mock.add_response(
        method='POST',
        url=BGG_LOGIN_URL,
        status_code=200,
        json={"success": True},
        headers={"set-cookie": "sessionid=abc; Path=/; HttpOnly"},
    )

    bgg = BggProvider()
    bgg.login("alice", "secret")

    # Cookie should be stored as a dict
    assert bgg._cookies == {"sessionid": "abc"}

    # Add a mocked GET endpoint and call an API method to ensure the cookie is sent
    httpx_mock.add_response(
        method='GET',
        url=f"{bgg._api.xml2}/search?query=whatever&type=boardgame&exact=1",
        status_code=200,
        text="<items total=\"0\"></items>",
    )

    bgg.boardgame_by_name("whatever")

    # Inspect recorded requests: ensure the GET request contains a Cookie header
    reqs = httpx_mock.get_requests()
    get_reqs = [r for r in reqs if r.method == "GET"]
    assert get_reqs, "No GET requests were recorded"
    last_get = get_reqs[-1]
    assert any(h.lower() == "cookie" for h in last_get.headers.keys()), "Cookie header not sent on authenticated request"


def test_authenticate_rejected_body_raises(httpx_mock):
    # Server returns 200 but body indicates rejection
    httpx_mock.add_response(
        method='POST',
        url=BGG_LOGIN_URL,
        status_code=200,
        json={"success": False, "error": "invalid credentials"},
    )

    bgg = BggProvider()
    with pytest.raises(ValueError):
        bgg.login("bob", "wrong")


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
        bgg.login("eve", "bad")
