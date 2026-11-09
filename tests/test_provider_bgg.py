import time

import pytest
from cartucho import ReturnCache

from carton.cache import load_cache, save_cache
from carton.models.boardgame import BGGDesigner
from carton.models.params import PlayersInterval
from carton.models.poll import MultilevelPoll, Poll
from carton.providers.bgg_provider import (
    BGG_API_URLS,
    BggProvider,
    BggUserNotFoundError,
    _parse_polls,
    _parse_polls_summary,
)


def test_parse_polls():
    poll_response = [
        {'@name': 'suggested_numplayers',
         '@title': 'User Suggested Number of Players',
         '@totalvotes': '2489',
         'results': [
            {'@numplayers': '1',
             'result': [{'@numvotes': '4', '@value': 'Best'},
                        {'@numvotes': '17', '@value': 'Recommended'},
                        {'@numvotes': '1531', '@value': 'Not Recommended'}]},
            {'@numplayers': '2',
             'result': [{'@numvotes': '118', '@value': 'Best'},
                        {'@numvotes': '396', '@value': 'Recommended'},
                        {'@numvotes': '1333', '@value': 'Not Recommended'}]},
            {'@numplayers': '3',
             'result': [{'@numvotes': '525', '@value': 'Best'},
                        {'@numvotes': '1311', '@value': 'Recommended'},
                        {'@numvotes': '237', '@value': 'Not Recommended'}]},
            {'@numplayers': '4',
             'result': [{'@numvotes': '1324', '@value': 'Best'},
                        {'@numvotes': '827', '@value': 'Recommended'},
                        {'@numvotes': '48', '@value': 'Not Recommended'}]},
            {'@numplayers': '5',
             'result': [{'@numvotes': '1194', '@value': 'Best'},
                        {'@numvotes': '882', '@value': 'Recommended'},
                        {'@numvotes': '63', '@value': 'Not Recommended'}]},
            {'@numplayers': '6',
             'result': [{'@numvotes': '535', '@value': 'Best'},
                        {'@numvotes': '1264', '@value': 'Recommended'},
                        {'@numvotes': '183', '@value': 'Not Recommended'}]},
            {'@numplayers': '7',
             'result': [{'@numvotes': '444', '@value': 'Best'},
                        {'@numvotes': '1179', '@value': 'Recommended'},
                        {'@numvotes': '325', '@value': 'Not Recommended'}]},
            {'@numplayers': '7+',
             'result': [{'@numvotes': '31', '@value': 'Best'},
                        {'@numvotes': '111', '@value': 'Recommended'},
                        {'@numvotes': '1040', '@value': 'Not Recommended'}]}]},
        {'@name': 'language_dependence',
         '@title': 'Language Dependence',
         '@totalvotes': '404',
         'results': {'result': [
            {'@level': '1',
             '@numvotes': '310',
             '@value': 'No necessary in-game text'},
            {'@level': '2',
             '@numvotes': '89',
             '@value': 'Some necessary text - easily memorized or small crib sheet'},
            {'@level': '3',
             '@numvotes': '4',
             '@value': 'Moderate in-game text - needs crib sheet or paste ups'},
            {'@level': '4',
             '@numvotes': '1',
             '@value': 'Extensive use of text - massive conversion needed to be playable'},
            {'@level': '5',
             '@numvotes': '0',
             '@value': 'Unplayable in another language'}]}},
        {'@name': 'suggested_playerage',
         '@title': 'User Suggested Player Age',
         '@totalvotes': '558',
         'results': {'result': [
            {'@numvotes': '0', '@value': '2'},
            {'@numvotes': '0', '@value': '3'},
            {'@numvotes': '1', '@value': '4'},
            {'@numvotes': '1', '@value': '5'},
            {'@numvotes': '22', '@value': '6'},
            {'@numvotes': '155', '@value': '8'},
            {'@numvotes': '227', '@value': '10'},
            {'@numvotes': '125', '@value': '12'},
            {'@numvotes': '23', '@value': '14'},
            {'@numvotes': '3', '@value': '16'},
            {'@numvotes': '1', '@value': '18'},
            {'@numvotes': '0', '@value': '21 and up'}]}}
    ]

    polls = _parse_polls(poll_response)
    assert polls['language_dependence'] == Poll(
        votes={
            '1': 310,
            '2': 89,
            '3': 4,
            '4': 1,
            '5': 0
        }
    )

    assert polls['suggested_playerage'] == Poll(
        votes={
            '2': 0,
            '3': 0,
            '4': 1,
            '5': 1,
            '6': 22,
            '8': 155,
            '10': 227,
            '12': 125,
            '14': 23,
            '16': 3,
            '18': 1,
            '21 and up': 0,
        }
    )

    assert polls['suggested_numplayers'] == MultilevelPoll(
        votes={
            '1': {
                'Best': 4,
                'Recommended': 17,
                'Not Recommended': 1531},
            '2': {
                'Best': 118,
                'Recommended': 396,
                'Not Recommended': 1333},
            '3': {
                'Best': 525,
                'Recommended': 1311,
                'Not Recommended': 237},
            '4': {
                'Best': 1324,
                'Recommended': 827,
                'Not Recommended': 48},
            '5': {
                'Best': 1194,
                'Recommended': 882,
                'Not Recommended': 63},
            '6': {
                'Best': 535,
                'Recommended': 1264,
                'Not Recommended': 183},
            '7': {
                'Best': 444,
                'Recommended': 1179,
                'Not Recommended': 325},
            '7+': {
                'Best': 31,
                'Recommended': 111,
                'Not Recommended': 1040}
        }
    )


def test_parse_poll_summary():
    poll_summary_response = {
        '@name': 'suggested_numplayers',
        '@title': 'User Suggested Number of Players',
        'result': [{'@name': 'bestwith',
                    '@value': 'Best with 4–5 players'},
                   {'@name': 'recommmendedwith',
                    '@value': 'Recommended with 3–7 players'}]
        }

    assert _parse_polls_summary(poll_summary_response) == {
        'suggested_numplayers': {
            'Best': PlayersInterval(lower=4, upper=5),
            'Recommended': PlayersInterval(lower=3, upper=7)
        }
    }


# MOCK_URL='https://mock.url'
#
#
# @pytest.mark.asyncio
# async def test_bgg_provider(httpx_mock: HTTPXMock):
#     httpx_mock.add_response(url=f"{MOCK_URL}/xmlapi2/search?query=Gloomhaven&type=boardgame&exact=1", text="""
# <?xml version="1.0" encoding="utf-8"?>
# <items total="4" termsofuse="https://boardgamegeek.com/xmlapi/termsofuse">
#     <item type="boardgame" id="291457">
#         <name type="primary" value="Gloomhaven: Jaws of the Lion"/>
#         <yearpublished value="2020" />
#     </item>
# </items>
# """)
#
#     bgg = BggProvider(url=MOCK_URL)
#     await bgg.boardgame_by_name("Gloomhaven")


BOARDGAME_XML_TEMPLATE = """<boardgames termsofuse="https://boardgamegeek.com/xmlapi/termsofuse">
  <boardgame objectid="{id}">
    <yearpublished>2024</yearpublished>
    <minplayers>2</minplayers>
    <maxplayers>6</maxplayers>
    <minplaytime>30</minplaytime>
    <maxplaytime>60</maxplaytime>
    <age>10</age>
    <name sortindex="1">Juego de prueba</name>
    <name primary="true" sortindex="1">Test Game</name>
    <boardgamecategory objectid="1042">Expansion for Base-game</boardgamecategory>
    {expansions}
    {designers}
    <poll name="suggested_numplayers" title="User Suggested Number of Players" totalvotes="1">
      {numplayers_results}
    </poll>
    <poll name="language_dependence" title="Language Dependence" totalvotes="0">
      <results>
        <result level="1" value="No necessary in-game text" numvotes="0" />
        <result level="2" value="Some necessary text" numvotes="0" />
      </results>
    </poll>
    <poll name="suggested_playerage" title="User Suggested Player Age" totalvotes="{age_votes}">
      {playerage_results}
    </poll>
    <statistics>
      <ratings>
        <usersrated>{users_rated}</usersrated>
        <average>{average}</average>
        <bayesaverage>{bayes_average}</bayesaverage>
        <ranks>
          {ranks}
        </ranks>
        <averageweight>0</averageweight>
      </ratings>
    </statistics>
  </boardgame>
</boardgames>
"""

PLAYERAGE_RESULTS = """<results>
        <result value="8" numvotes="1" />
        <result value="10" numvotes="3" />
      </results>"""


# Best, Recommended and Not Recommended votes for each number of players
NUMPLAYERS_VOTES = {'2': (1, 0, 0), '3': (0, 1, 0)}


def _numplayers_results(votes: dict[str, tuple[int, int, int]]) -> str:
    return ''.join(
        f'''<results numplayers="{numplayers}">
        <result value="Best" numvotes="{best}" />
        <result value="Recommended" numvotes="{recommended}" />
        <result value="Not Recommended" numvotes="{not_recommended}" />
      </results>'''
        for numplayers, (best, recommended, not_recommended) in votes.items())


RANKS = """<rank type="subtype" id="1" name="boardgame" friendlyname="Board Game Rank" value="624"
                bayesaverage="6.90096" />
          <rank type="family" id="5497" name="strategygames" friendlyname="Strategy Game Rank" value="599"
                bayesaverage="6.76951" />"""


def _boardgame_xml(id: int, designers: str = '', playerage_results: str = PLAYERAGE_RESULTS,
                   numplayers_votes: dict[str, tuple[int, int, int]] = NUMPLAYERS_VOTES,
                   users_rated: int = 145300, average: float = 7.08977, bayes_average: float = 6.90096,
                   ranks: str = RANKS, expansions: str = '') -> str:
    return BOARDGAME_XML_TEMPLATE.format(
        id=id, designers=designers, expansions=expansions, playerage_results=playerage_results,
        age_votes=4 if playerage_results else 0,
        numplayers_results=_numplayers_results(numplayers_votes),
        users_rated=users_rated, average=average, bayes_average=bayes_average, ranks=ranks)


def _boardgame_url(id: int) -> str:
    return f"{BGG_API_URLS.xml}/boardgame/{id}?stats=1"


@pytest.mark.parametrize('designers, expected', [
    ('', set()),
    ('<boardgamedesigner objectid="108280">David Amorin</boardgamedesigner>',
     {BGGDesigner(name='David Amorin', bgg_id=108280)}),
    (('<boardgamedesigner objectid="2">Reiner Knizia</boardgamedesigner>'
      '<boardgamedesigner objectid="3">Bruno Cathala</boardgamedesigner>'),
     {BGGDesigner(name='Reiner Knizia', bgg_id=2), BGGDesigner(name='Bruno Cathala', bgg_id=3)}),
])
async def test_boardgame_by_id_designers(httpx_mock, designers, expected):
    # Some games (e.g. many expansions) have no designer credited in BGG, so the
    # response contains no <boardgamedesigner> element at all
    httpx_mock.add_response(url=_boardgame_url(439687), text=_boardgame_xml(439687, designers=designers))

    async with BggProvider() as bgg:
        boardgame = await bgg.boardgame_by_id(439687)

    assert boardgame.name == 'Test Game'
    assert {(d.name, d.bgg_id) for d in boardgame.designers} == {(d.name, d.bgg_id) for d in expected}


async def test_boardgame_by_id_with_empty_poll(httpx_mock):
    # Polls without votes may come without any <results> element
    httpx_mock.add_response(url=_boardgame_url(433986), text=_boardgame_xml(433986, playerage_results=''))

    async with BggProvider() as bgg:
        boardgame = await bgg.boardgame_by_id(433986)

    assert boardgame.name == 'Test Game'
    assert boardgame.community_min_age is None


async def test_boardgame_by_id_community_min_age(httpx_mock):
    httpx_mock.add_response(url=_boardgame_url(1), text=_boardgame_xml(1))

    async with BggProvider() as bgg:
        boardgame = await bgg.boardgame_by_id(1)

    assert boardgame.community_min_age == 10


async def test_boardgame_by_id_uses_cache(httpx_mock, tmp_path):
    # The game is requested once, later calls use the cache
    httpx_mock.add_response(url=_boardgame_url(1), text=_boardgame_xml(1))
    cache = ReturnCache()

    async with BggProvider(return_cache=cache) as bgg:
        first = await bgg.boardgame_by_id(1)
        second = await bgg.boardgame_by_id(1)
    assert first == second

    # The saved cache is reused by other providers
    save_cache(cache, tmp_path / 'cache.pickle')
    async with BggProvider(return_cache=load_cache(tmp_path / 'cache.pickle')) as bgg:
        assert await bgg.boardgame_by_id(1) == first

    assert len(httpx_mock.get_requests()) == 1


async def test_boardgame_by_id_cache_per_url(httpx_mock):
    httpx_mock.add_response(url=_boardgame_url(1), text=_boardgame_xml(1), is_reusable=True)
    cache = ReturnCache()

    async with BggProvider(return_cache=cache) as bgg:
        await bgg.boardgame_by_id(1)
    async with BggProvider(url='https://other.example.com', return_cache=cache) as bgg:
        await bgg.boardgame_by_id(1)

    assert len(httpx_mock.get_requests()) == 2


def test_load_cache_missing_or_broken(tmp_path):
    assert len(load_cache(tmp_path / 'missing.pickle')) == 0

    broken = tmp_path / 'broken.pickle'
    broken.write_bytes(b'not a pickle')
    assert len(load_cache(broken)) == 0


def test_parse_polls_without_results():
    poll_response = [
        {'@name': 'language_dependence', '@title': 'Language Dependence', '@totalvotes': '0',
         'results': {'result': [{'@level': '1', '@numvotes': '0', '@value': 'No necessary in-game text'}]}},
        {'@name': 'suggested_playerage', '@title': 'User Suggested Player Age', '@totalvotes': '0'},
        {'@name': 'suggested_numplayers', '@title': 'User Suggested Number of Players', '@totalvotes': '0'},
    ]

    polls = _parse_polls(poll_response)

    assert polls['language_dependence'] == Poll(votes={'1': 0})
    assert 'suggested_playerage' not in polls
    assert 'suggested_numplayers' not in polls


async def test_boardgame_by_id_players(httpx_mock):
    httpx_mock.add_response(url=_boardgame_url(1), text=_boardgame_xml(1))

    async with BggProvider() as bgg:
        boardgame = await bgg.boardgame_by_id(1)

    assert str(boardgame.players) == '2-6'


@pytest.mark.parametrize('numplayers_votes, expected_players, expected_best_players', [
    # Recommended when Best + Recommended > Not Recommended, best when Best > Recommended + Not Recommended,
    # the same rules BGG uses in its poll summary. Open ended counts such as '5+' are ignored
    ({'1': (0, 1, 5), '2': (10, 2, 0), '3': (3, 8, 1), '4': (1, 2, 9), '5': (6, 3, 1), '5+': (9, 0, 0)},
     '2-3, 5', '2, 5'),
    # If no number of players has a majority of Best votes, the most voted ones are taken
    ({'2': (2, 2, 0), '3': (1, 2, 0)}, '2-3', '2'),
    # Without votes there is no community information
    ({'2': (0, 0, 0), '3': (0, 0, 0)}, None, None),
])
async def test_boardgame_by_id_community_players(httpx_mock, numplayers_votes,
                                                 expected_players, expected_best_players):
    httpx_mock.add_response(url=_boardgame_url(1), text=_boardgame_xml(1, numplayers_votes=numplayers_votes))

    async with BggProvider() as bgg:
        boardgame = await bgg.boardgame_by_id(1)

    assert (str(boardgame.community_players) if boardgame.community_players else None) == expected_players
    assert (str(boardgame.community_best_players) if boardgame.community_best_players else None) == \
        expected_best_players


NOT_RANKED = ('<rank type="subtype" id="1" name="boardgame" friendlyname="Board Game Rank" value="Not Ranked" '
              'bayesaverage="Not Ranked" />')


@pytest.mark.parametrize('xml_args, expected', [
    ({}, {'rating': 7.08977, 'geek_rating': 6.90096, 'num_ratings': 145300, 'rank': 624}),
    # Games not ranked yet, such as many expansions
    ({'ranks': NOT_RANKED},
     {'rating': 7.08977, 'geek_rating': 6.90096, 'num_ratings': 145300, 'rank': None}),
    # Games with too few ratings have no geek rating, BGG returns 0 for it
    ({'users_rated': 12, 'bayes_average': 0, 'ranks': NOT_RANKED},
     {'rating': 7.08977, 'geek_rating': None, 'num_ratings': 12, 'rank': None}),
    # Without ratings BGG returns 0 as average and geek rating
    ({'users_rated': 0, 'average': 0, 'bayes_average': 0, 'ranks': NOT_RANKED},
     {'rating': None, 'geek_rating': None, 'num_ratings': 0, 'rank': None}),
])
async def test_boardgame_by_id_ratings_and_rank(httpx_mock, xml_args, expected):
    httpx_mock.add_response(url=_boardgame_url(1), text=_boardgame_xml(1, **xml_args))

    async with BggProvider() as bgg:
        boardgame = await bgg.boardgame_by_id(1)

    assert boardgame.model_dump(include=set(expected)) == expected


@pytest.mark.parametrize('expansions, expected', [
    ('', False),
    # Base games link their expansions without the inbound attribute
    ('<boardgameexpansion objectid="2">Test Game: Expansion</boardgameexpansion>', False),
    # Expansions link their base games as inbound
    ('<boardgameexpansion objectid="3" inbound="true">Test Game</boardgameexpansion>', True),
    (('<boardgameexpansion objectid="3" inbound="true">Test Game</boardgameexpansion>'
      '<boardgameexpansion objectid="4" inbound="true">Test Game: Big Box</boardgameexpansion>'), True),
])
async def test_boardgame_by_id_is_expansion(httpx_mock, expansions, expected):
    httpx_mock.add_response(url=_boardgame_url(1), text=_boardgame_xml(1, expansions=expansions))

    async with BggProvider() as bgg:
        boardgame = await bgg.boardgame_by_id(1)

    assert boardgame.is_expansion is expected


def _collection_xml(*ids: int) -> str:
    items = ''.join(f'<item objecttype="thing" objectid="{id}" subtype="boardgame" collid="{id}" />'
                    for id in ids)
    return f'<items totalitems="{len(ids)}" termsofuse="https://boardgamegeek.com/xmlapi/termsofuse">{items}</items>'


def _collection_url(params: str) -> str:
    return f"{BGG_API_URLS.xml2}/collection?username=alice&own=1&brief=1&{params}"


@pytest.mark.parametrize('base_ids, expansion_ids, expected', [
    ((1, 2), (3,), [1, 2, 3]),
    ((1, 2, 1), (), [1, 2]),
    ((), (3,), [3]),
    ((), (), []),
])
async def test_user_collection_ids_includes_expansions(httpx_mock, base_ids, expansion_ids, expected):
    httpx_mock.add_response(url=_collection_url('excludesubtype=boardgameexpansion'),
                            text=_collection_xml(*base_ids))
    httpx_mock.add_response(url=_collection_url('subtype=boardgameexpansion'),
                            text=_collection_xml(*expansion_ids))

    async with BggProvider() as bgg:
        assert await bgg._user_collection_ids('alice') == expected


async def test_user_collection_ids_unknown_user(httpx_mock):
    errors_xml = '<errors><error><message>Invalid username specified</message></error></errors>'
    httpx_mock.add_response(url=_collection_url('excludesubtype=boardgameexpansion'), text=errors_xml)
    httpx_mock.add_response(url=_collection_url('subtype=boardgameexpansion'), text=errors_xml)

    async with BggProvider() as bgg:
        with pytest.raises(BggUserNotFoundError):
            await bgg._user_collection_ids('alice')


async def test_user_collection_cached_games_are_not_rate_limited(httpx_mock):
    # Only requests to BGG are rate limited, so a cached collection is returned immediately
    ids = range(1, 31)
    httpx_mock.add_response(url=_collection_url('excludesubtype=boardgameexpansion'),
                            text=_collection_xml(*ids), is_reusable=True)
    httpx_mock.add_response(url=_collection_url('subtype=boardgameexpansion'),
                            text=_collection_xml(), is_reusable=True)
    for id in ids:
        httpx_mock.add_response(url=_boardgame_url(id), text=_boardgame_xml(id))

    async with BggProvider(return_cache=ReturnCache()) as bgg:
        first = await bgg.user_collection('alice')

        start = time.monotonic()
        second = await bgg.user_collection('alice')
        assert time.monotonic() - start < 0.5

    assert second == first
    assert len(httpx_mock.get_requests()) == 2 + len(ids) + 2
