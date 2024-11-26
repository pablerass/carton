import aiometer
import httpx
import logging
import xmltodict

from collections import namedtuple
from functools import partial
from pydantic import ValidationError

from ..models.boardgame import BGGGame, BGGDesigner
from ..models.params import Players, PlayTime, MinAge, Year
from ..models.poll import Poll, MultilevelPoll


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

    async def boardgame_by_id(self, id: int | str) -> BGGGame:
        logger = logging.getLogger('carton.BggProvider.boardgame_by_id')

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._api.xml}/boardgame/{id}")

            logger.debug(f"Found game {id}")
            try:
                boardgame_response = xmltodict.parse(response.text)['boardgames']['boardgame']

                name_info = boardgame_response['name']
                if not isinstance(name_info, list):
                    name_info = [name_info]
                name = [name['#text'] for name in name_info if name.get('@primary', False)][0]

                designer_info = boardgame_response['boardgamedesigner']
                if not isinstance(designer_info, list):
                    designer_info = [designer_info]
                designers = [BGGDesigner(name=designer['#text'], bgg_id=designer['@objectid'])
                             for designer in designer_info]

                poll_info = boardgame_response['poll']
                polls = {poll['@name']: poll['results'] for poll in poll_info}
                poll_age = Poll.from_list(polls['suggested_playerage']['result'], '@value', '@numvotes')
                poll_players = MultilevelPoll.from_list(
                    polls['suggested_numplayers'],
                    choice_1_key='@numplayers', votes_1_key='result',
                    choice_2_key='@value', votes_2_key='@numvotes')

                min_age = MinAge(boardgame_response['age'])
                # TUNE: It would be better to execute MinAge validation
                if not 0 < min_age:
                    min_age = None
                    logger.warning(f'Unable to obtain min_age for {name}')

                players = None
                try:
                    players = Players(lower=boardgame_response['minplayers'],
                                      upper=boardgame_response['maxplayers'])
                except ValidationError:
                    logger.warning(f'Unable to obtain players for {name}')

                play_time = None
                try:
                    play_time = PlayTime(lower=boardgame_response['minplaytime'],
                                         upper=boardgame_response['maxplaytime'])
                except ValidationError:
                    logger.warning(f'Unable to obtain play_time for {name}')

                published = None
                try:
                    published = Year(boardgame_response['yearpublished'])
                except ValidationError:
                    logger.warning(f'Unable to obtain year for {name}')

                community_min_age = None
                try:
                    poll_values = poll_age.winner()
                    community_min_age = MinAge(poll_values)
                except ValidationError:
                    logger.warning(f'Unable to obtain community_min_age with {poll_values} for {name}')

                # TODO: Load community info as set of values instead of interval
                community_players = None
                try:
                    poll_values = (poll_players.choice_2_poll('Best') +
                                   poll_players.choice_2_poll('Recommended')).winners()
                    community_players = Players.from_list(poll_values)
                except ValidationError:
                    logger.warning(f'Unable to obtain community_players with {poll_values} for {name}')

                community_best_players = None
                try:
                    poll_values = poll_players.winners('Best')
                    community_best_players = Players.from_list(poll_values)
                except ValidationError:
                    logger.warning(f'Unable to obtain community_best_players with {poll_values} for {name}')

                boardgame = BGGGame(
                    name=name,
                    designers=designers,
                    min_age=min_age,
                    players=players,
                    play_time=play_time,
                    published=published,
                    bgg_id=id,
                    community_min_age=community_min_age,
                    community_players=community_players,
                    community_best_players=community_best_players
                )
            except Exception as e:
                logger.error(f"Error obtaining {id} boardgame from response")
                raise e

            logger.info(f"Obtained boardgame {boardgame.name} with id {id}")
            return boardgame

    async def boardgame_by_name(self, name: str):
        logger = logging.getLogger('carton.BggProvider.boardgame_by_name')

        async with httpx.AsyncClient() as client:
            # TODO: Extract this to a search method
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

    async def user_collection(self, user: str):
        logger = logging.getLogger('carton.BggProvider.user_collection')

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api.xml2}/collection",
                params={'username': user, 'own': 1})

            response_items = xmltodict.parse(response.text)['items']
            logger.debug(f"Found {response_items['@totalitems']} games in {user} collection")

            boardgame_ids = [i['@objectid'] for i in response_items['item'] if i['@subtype'] == 'boardgame']
            return await aiometer.run_all(
                [partial(self.boardgame_by_id, id) for id in boardgame_ids],
                max_at_once=20,
                max_per_second=10)
