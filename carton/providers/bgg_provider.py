import asyncio
import logging
from collections import namedtuple
from functools import partial
from typing import Self

import aiometer
import httpx
import xmltodict
from pydantic import ValidationError

from ..models.boardgame import BGGDesigner, BGGGame
from ..models.params import MinAge, Players, PlayersInterval, PlayTime, Year
from ..models.poll import MultilevelPoll, Poll

BggApiUrlMap = namedtuple('_BggApiUrl', ['xml', 'xml2', 'json'])

BGG_URL: str = "https://boardgamegeek.com"
BGG_LOGIN_URL: str = "https://boardgamegeek.com/login/api/v1"

# Retry policy for 202 Accepted responses, returned by BGG while a request is queued
BGG_ACCEPTED_RETRIES: int = 5
BGG_ACCEPTED_DELAY: float = 2.0  # Seconds, doubled on each retry

BGG_API_URLS: BggApiUrlMap = BggApiUrlMap(
    xml=f"{BGG_URL}/xmlapi",
    xml2=f"{BGG_URL}/xmlapi2",
    json=f"{BGG_URL}/api"
)


def _as_list(value) -> list:
    """Normalize an xmltodict node that may be missing, a single element or a list of elements."""
    if value is None:
        return []
    if not isinstance(value, list):
        return [value]
    return value


def _parse_polls(polls_response: list[dict]) -> dict[str, Poll]:
    # Polls without votes may come without any <results> element, those are skipped
    polls = {poll['@name']: poll['results']
             for poll in _as_list(polls_response) if poll.get('results')}

    if 'language_dependence' in polls:
        polls['language_dependence'] = Poll.from_list(
            _as_list(polls['language_dependence']['result']), '@level', '@numvotes')
    if 'suggested_numplayers' in polls:
        polls['suggested_numplayers'] = MultilevelPoll.from_list(
            [{**results, 'result': _as_list(results['result'])}
             for results in _as_list(polls['suggested_numplayers'])],
            choice_1_key='@numplayers', votes_1_key='result',
            choice_2_key='@value', votes_2_key='@numvotes')
    if 'suggested_playerage' in polls:
        polls['suggested_playerage'] = Poll.from_list(
            _as_list(polls['suggested_playerage']['result']), '@value', '@numvotes')

    return polls


def _community_players(numplayers_poll: MultilevelPoll) -> tuple[Players | None, Players | None]:
    """Obtain recommended and best numbers of players from the suggested number of players poll.

    Uses the same rules as the BGG poll summary: a number of players is recommended when
    Best + Recommended votes outnumber Not Recommended ones, and best when Best votes outnumber
    the rest. If no number of players has a majority of Best votes, the most voted ones are taken.
    Open ended choices such as '7+' are ignored, as they cannot be represented as intervals.
    """
    votes = {int(numplayers): choice_votes for numplayers, choice_votes in numplayers_poll.votes.items()
             if str(numplayers).isdigit()}

    recommended = [numplayers for numplayers, v in votes.items()
                   if v['Best'] + v['Recommended'] > v['Not Recommended']]

    best = [numplayers for numplayers, v in votes.items()
            if v['Best'] > v['Recommended'] + v['Not Recommended']]
    if not best:
        max_best = max((v['Best'] for v in votes.values()), default=0)
        if max_best > 0:
            best = [numplayers for numplayers, v in votes.items() if v['Best'] == max_best]

    return (Players.from_values(recommended) if recommended else None,
            Players.from_values(best) if best else None)


def _parse_polls_summary(polls_summary_response: dict) -> dict[str, str]:
    if isinstance(polls_summary_response, dict):
        polls_summary_response = [polls_summary_response]

    polls_summary = {poll_summary['@name']: poll_summary['result']
                     for poll_summary in polls_summary_response}

    polls_summary['suggested_numplayers'] = {
        value[0]: PlayersInterval.from_list(
            items=[int(n) for n in value[2].split('–')])  # WARN: Not a standard hyphen '-'
        for value in [result['@value'].split(' ') for result in polls_summary['suggested_numplayers']]
    }

    return polls_summary


class BggProvider:
    def __init__(self, url: str = BGG_URL, api_key: str | None = None,
                 api_urls: BggApiUrlMap = BGG_API_URLS) -> None:
        self.__url: str = url
        self.__api: BggApiUrlMap = api_urls

        # Stored auth cookies after successful authentication (None if not authenticated)
        self.__auth_cookies: dict | None = None
        self.__auth_headers: dict | None = None
        self.__client: httpx.AsyncClient | None = None

        # If an API key/token is provided at construction time, activate it
        if api_key:
            self.api_login(api_key)

    def api_login(self, api_key: str) -> None:
        """Register an application token for subsequent requests.

        The XML API requires an Authorization header in the format:
        Authorization: Bearer <token>
        Accepts either the raw token or a string already prefixed with "Bearer ".
        """
        token = api_key.strip()
        # Allow callers to pass either the raw token or the full 'Bearer <token>' value
        if token.lower().startswith('bearer '):
            token = token.split(' ', 1)[1]
        self.__auth_headers = {'Authorization': f'Bearer {token}'}

    def user_login(self, username: str, password: str) -> None:
        """Login to BoardGameGeek and store session cookies for subsequent requests.

        Sends a JSON payload {"credentials": {"username": username, "password": password}}
        to the BGG login endpoint and stores returned cookies in `self._auth_cookies`.
        Raises httpx.HTTPStatusError on non-2xx responses or ValueError if the login is rejected.
        """
        logger = logging.getLogger('carton.BggProvider.login')

        with httpx.Client() as client:
            response = client.post(BGG_LOGIN_URL, json={"credentials": {"username": username, "password": password}})
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                logger.error(f"Authentication request failed with status {response.status_code}: {response.text[:200]}")
                raise

            # Convert cookies to a simple dict for reuse in future requests
            self.__auth_cookies = dict(response.cookies)

            logger.debug(f"Authenticated as {username}")

    def logout(self) -> None:
        """Clear stored authentication and remove it from the HTTP client, if already created."""
        if self.__client is not None:
            for header in self.__auth_headers or {}:
                self.__client.headers.pop(header, None)
            for cookie in self.__auth_cookies or {}:
                self.__client.cookies.delete(cookie)

        self.__auth_cookies = None
        self.__auth_headers = None

    @property
    def _api(self) -> BggApiUrlMap:
        return self.__api

    @property
    def url(self) -> str:
        return self.__url

    @property
    def _auth_cookies(self) -> dict | None:
        return self.__auth_cookies

    @property
    def _auth_headers(self) -> dict | None:
        return self.__auth_headers

    @property
    def _client(self) -> httpx.AsyncClient:
        """Shared HTTP client, so all requests reuse the same connection pool.

        The client is created on first use and the current auth is added on every
        access, so a later login applies to it. Logout removes it in `logout`.
        """
        if self.__client is None:
            self.__client = httpx.AsyncClient()

        if self._auth_headers:
            self.__client.headers.update(self._auth_headers)
        if self._auth_cookies:
            self.__client.cookies.update(self._auth_cookies)

        return self.__client

    async def aclose(self) -> None:
        """Close the shared HTTP client. A new one is created if the provider is used again."""
        if self.__client is not None:
            await self.__client.aclose()
            self.__client = None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.aclose()

    async def _get(self, url: str, params: dict | None = None,
                   retries: int = BGG_ACCEPTED_RETRIES,
                   delay: float = BGG_ACCEPTED_DELAY) -> httpx.Response:
        """GET a BGG API URL, retrying with exponential backoff while BGG answers 202 Accepted.

        BGG returns 202 when a request has been queued for processing (e.g. large
        collections) and the actual data has to be requested again later.
        """
        logger = logging.getLogger('carton.BggProvider._get')

        for attempt in range(retries + 1):
            response = await self._client.get(url, params=params)
            response.raise_for_status()

            if response.status_code != 202:
                return response

            if attempt < retries:
                wait = delay * 2 ** attempt
                logger.debug(f"Request to {url} queued by BGG, retrying in {wait}s")
                await asyncio.sleep(wait)

        raise TimeoutError(f"BGG kept the request to {url} queued after {retries} retries")

    async def hot(self):
        response = await self._get(f"{self._api.xml2}/hot")
        # TODO: Return the right response
        print(response.text)

    async def boardgame_by_id(self, id: int | str) -> BGGGame:
        logger = logging.getLogger('carton.BggProvider.boardgame_by_id')

        response = await self._get(
            f"{self._api.xml}/boardgame/{id}",
            params={'stats': 1})

        logger.debug(f"Found game {id}")
        try:
            boardgame_response = xmltodict.parse(response.text)['boardgames']['boardgame']

            name_info = boardgame_response['name']
            if not isinstance(name_info, list):
                name_info = [name_info]
            name = next(name['#text'] for name in name_info if name.get('@primary', False))

            # Some games (e.g. many expansions) have no designer credited
            designers = [BGGDesigner(name=designer['#text'], bgg_id=designer['@objectid'])
                         for designer in _as_list(boardgame_response.get('boardgamedesigner'))]

            polls = _parse_polls(boardgame_response.get('poll'))
            # TODO: Readd this
            # poll_summary = _parse_polls_summary(boardgame_response['poll-summary'])

            min_age = MinAge(boardgame_response['age'])
            # TUNE: It would be better to execute MinAge validation
            if not 0 < min_age:
                min_age = None
                logger.warning(f'Unable to obtain min_age for {name}')

            players = None
            try:
                players = Players(intervals=[PlayersInterval(lower=boardgame_response['minplayers'],
                                                             upper=boardgame_response['maxplayers'])])
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
            if 'suggested_playerage' in polls:
                try:
                    poll_values = polls['suggested_playerage'].winner()
                    community_min_age = MinAge(poll_values)
                except ValidationError:
                    logger.warning(f'Unable to obtain community_min_age with {poll_values} for {name}')

            community_players = None
            community_best_players = None
            if 'suggested_numplayers' in polls:
                community_players, community_best_players = _community_players(polls['suggested_numplayers'])

            # from pprint import pprint
            # pprint(boardgame_response)
            community_average_weight = boardgame_response['statistics']['ratings']['averageweight']

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
                community_best_players=community_best_players,
                community_average_weight=community_average_weight
            )
        except Exception:
            logger.error(f"Error obtaining {id} boardgame from response")
            raise

        logger.info(f"Obtained boardgame {boardgame.name} with id {id}")
        return boardgame

    async def boardgame_by_name(self, name: str) -> BGGGame:
        logger = logging.getLogger('carton.BggProvider.boardgame_by_name')

        # TODO: Extract this to a search method
        response = await self._get(
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
        except Exception:
            logger.error(f"Error obtaining '{name}' boardgame id from response {response.text}")
            raise

        logger.info(f"Obtained {boardgame_id} for '{name}' boardgame")
        return await self.boardgame_by_id(boardgame_id)

    async def _user_collection_ids(self, user: str) -> list[int]:
        # TUNE: Include retries for rate limits (429)
        response = await self._get(
            f"{self._api.xml2}/collection",
            params={'username': user, 'own': 1, 'brief': 1})

        response_items = xmltodict.parse(response.text)['items']

        boardgame_ids = [i['@objectid'] for i in response_items['item']
                         if i['@subtype'] in ('boardgame', 'boardgameexpansion')]
        return boardgame_ids

    async def user_collection(self, user: str):
        logger = logging.getLogger('carton.BggProvider.user_collection')

        boardgame_ids = await self._user_collection_ids(user)
        logger.debug(f"Found {len(boardgame_ids)} games and expansions in {user} collection")
        return await aiometer.run_all(
            [partial(self.boardgame_by_id, id) for id in boardgame_ids],
            max_at_once=20,
            max_per_second=10)
