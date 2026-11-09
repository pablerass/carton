import pytest

from carton.models.boardgame import BGGDesigner
from carton.models.params import PlayersInterval
from carton.models.poll import MultilevelPoll, Poll
from carton.providers.bgg_provider import BGG_API_URLS, BggProvider, _parse_polls, _parse_polls_summary


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


def _boardgame_xml(id: int, designers: str = '', playerage_results: str = PLAYERAGE_RESULTS,
                   numplayers_votes: dict[str, tuple[int, int, int]] = NUMPLAYERS_VOTES) -> str:
    return BOARDGAME_XML_TEMPLATE.format(
        id=id, designers=designers, playerage_results=playerage_results,
        age_votes=4 if playerage_results else 0,
        numplayers_results=_numplayers_results(numplayers_votes))


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
