import httpx
import logging
import xmltodict

from collections import namedtuple

from ..models.boardgame import BGGGame, Designer
from ..models.params import PlayersRange, PlayTimeRange, MinAge


BGG_URL: str = "https://boardgamegeek.com"


_BggApiUrl: namedtuple = namedtuple('_BggApiUrl', ['xml', 'xml2', 'json'])


class BggProvider:
    def __init__(self, url: str = BGG_URL):
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
        # TODO: Move the client class level
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._api.xml2}/hot")
            # TODO: Return the right response
            print(response.text)

    async def boardgame_by_id(self, id: int | str):
        logger = logging.getLogger('carton.BggProvider.boardgame_by_id')

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._api.xml}/boardgame/{id}")

            # TUNE: Remove of format better this log line
            logger.debug(f"Found {response.text} games for name {id}")
            try:
                boardgame_response = xmltodict.parse(response.text)['boardgames']['boardgame']

                # TODO: Allow multiple designers
                if isinstance(boardgame_response['boardgamedesigner'], list):
                    designer = boardgame_response['boardgamedesigner'][0]['#text']
                else:
                    designer = boardgame_response['boardgamedesigner']['#text']

                boardgame = BGGGame(
                    boardgame_response['name'][0]['#text'],
                    id=id,
                    designer=Designer(designer),
                    min_age=MinAge(boardgame_response['age']),
                    players=PlayersRange(boardgame_response['minplayers'], boardgame_response['maxplayers']),
                    play_time=PlayTimeRange(boardgame_response['minplaytime'], boardgame_response['maxplaytime']))
            except Exception as e:
                logger.error(f"Error obtaining {id} boardgame from response {response.text}")
                return e

            logger.info(f"Obtained boardgame {boardgame} from id {id}")
            return boardgame

    async def boardgame_by_name(self, name: str):
        logger = logging.getLogger('carton.BggProvider.boardgame_by_name')

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api.xml2}/search",
                params={'query': name, 'type': 'boardgame', 'exact': 1})

            # TUNE: Remove of format better this log line
            logger.debug(f"Found {response.text} games for name {name}")
            try:
                response_items = xmltodict.parse(response.text)['items']
                match (int(response_items['@total'])):
                    case 0:
                        # TUNE: Return none if no game was found
                        logger.warning(f"No boardgame found for '{name}'")
                        return None
                    case 1:
                        boardgame_id = response_items['item']['@id']
                    case _:
                        # TUNE: At the moment, return the first one. This happens in
                        # games with multiple versions such as Citadels
                        logger.warning(f"More than one boardgame found for '{name}'")
                        boardgame_id = response_items['item'][0]['@id']
            except Exception as e:
                logger.error(f"Error obtaining '{name}' boardgame id from response {response.text}")
                raise e

            logger.info(f"Obtained {boardgame_id} for '{name}' boardgame")
            return await self.boardgame_by_id(boardgame_id)
