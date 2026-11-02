import httpx
import pytest

from carton.providers.bgg_provider import BggProvider, BGG_API_URLS


HOT_URL = f"{BGG_API_URLS.xml2}/hot"


@pytest.mark.asyncio
async def test_get_retries_while_accepted(httpx_mock):
    httpx_mock.add_response(url=HOT_URL, status_code=202)
    httpx_mock.add_response(url=HOT_URL, status_code=202)
    httpx_mock.add_response(url=HOT_URL, status_code=200, text="<items/>")

    async with BggProvider() as bgg:
        response = await bgg._get(HOT_URL, delay=0)

    assert response.status_code == 200
    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_get_gives_up_after_retries(httpx_mock):
    httpx_mock.add_response(url=HOT_URL, status_code=202, is_reusable=True)

    async with BggProvider() as bgg:
        with pytest.raises(TimeoutError):
            await bgg._get(HOT_URL, retries=2, delay=0)

    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_get_raises_on_error_status(httpx_mock):
    httpx_mock.add_response(url=HOT_URL, status_code=500)

    async with BggProvider() as bgg:
        with pytest.raises(httpx.HTTPStatusError):
            await bgg._get(HOT_URL)


@pytest.mark.asyncio
async def test_client_is_shared_and_closed():
    bgg = BggProvider()
    async with bgg:
        client = bgg._client
        assert bgg._client is client

    assert client.is_closed
    # A new client is created if the provider is used again
    assert bgg._client is not client
    await bgg.aclose()


@pytest.mark.asyncio
async def test_auth_changes_apply_to_existing_client(httpx_mock):
    httpx_mock.add_response(url=HOT_URL, status_code=200, is_reusable=True)

    async with BggProvider() as bgg:
        await bgg._get(HOT_URL)
        bgg.api_login("token")
        await bgg._get(HOT_URL)
        bgg.logout()
        await bgg._get(HOT_URL)

    first, logged_in, logged_out = httpx_mock.get_requests()
    assert 'Authorization' not in first.headers
    assert logged_in.headers['Authorization'] == 'Bearer token'
    assert 'Authorization' not in logged_out.headers
