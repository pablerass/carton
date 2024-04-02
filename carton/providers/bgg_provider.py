import httpx
import xmltodict

from collections import namedtuple

from ..models.boardgame import BGGGame, Designer
from ..models.params import PlayersRange, PlayTimeRange, MinAge


BGG_URL: str = "https://boardgamegeek.com"


_BggApiUrl: namedtuple = namedtuple('_BggApiUrl', ['xml', 'xml2', 'json'])


class BggProvider:
    def __init__(self, url=BGG_URL):
        self.__url = url
        self.__api = _BggApiUrl(
            xml=f"{url}/xmlapi",
            xml2=f"{url}/xmlapi2",
            json=f"{url}/api"
        )

    @property
    def url(self) -> str:
        return self.__url

    @property
    def _api(self) -> str:
        return self.__api

    async def hot(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._api.xml2}/hot")
            print(response.text)

    async def boardgame_by_id(self, id: int | str):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._api.xml}/boardgame/{id}")
            boardgame_response = xmltodict.parse(response.text)['boardgames']['boardgame']

            return BGGGame(
                boardgame_response['name'][0]['#text'],
                id=id,
                designer=Designer(boardgame_response['boardgamedesigner']['#text']),
                min_age=MinAge(boardgame_response['age']),
                players=PlayersRange(boardgame_response['minplayers'], boardgame_response['maxplayers']),
                play_time=PlayTimeRange(boardgame_response['minplaytime'], boardgame_response['maxplaytime']))

    async def boardgame_by_name(self, name: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api.xml2}/search",
                params={'query': name, 'type': 'boardgame', 'exact': 1})

            reponse_items = xmltodict.parse(response.text)['items']
            if not int(reponse_items['@total']):
                return None

            boardgame_id = reponse_items['item']['@id']

            return await self.boardgame_by_id(boardgame_id)
