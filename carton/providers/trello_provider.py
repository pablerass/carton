import asyncio
import httpx


TRELLO_API_URL: str = "https://api.trello.com/1"


# def _id_or_name(id: str = None, name: str = None) -> str:


def _member_or_me(member: str = None) -> str:
    if member is None:
        return "me"
    return member


class TrelloProvider:
    def __init__(self, api_key: str, api_token: str, api_url: str = TRELLO_API_URL):
        self.__api_url = api_url

        self.__api_key = api_key
        self.__api_token = api_token

        self.__client = None

    @property
    def api_url(self):
        return self.__api_url

    @property
    def _client(self) -> httpx.AsyncClient:
        if self.__client is None:
            self.__client = httpx.AsyncClient(
                headers={'Accept': 'application/json'},
                params={'key': self.__api_key, 'token': self.__api_token},
                transport=httpx.AsyncHTTPTransport(retries=3))

        return self.__client

    async def _close_client(self):
        await self.__client.aclose()

    def __del__(self):
        if self.__client is None:
            # TUNE: It seems that close is async
            asyncio.run(self._close_client())

    async def member(self, id: str = None) -> dict:
        member = _member_or_me(id)
        response = await self._client.get(f"{self.api_url}/members/{member}")
        from pprint import pprint
        pprint(response.json())

    async def boards(self, member: str = None) -> list[dict]:
        member = _member_or_me(member)
        response = await self._client.get(f"{self.api_url}/members/{member}/boards")
        return response.json()

    async def board_lists(self, board_id: str = None) -> dict:
        response = await self._client.get(f"{self.api_url}/boards/{board_id}/lists")
        return response.json()

    async def list_cards(self, list_id: str = None) -> dict:
        response = await self._client.get(f"{self.api_url}/lists/{list_id}/cards")
        return response.json()
