# import pytest
#
# from pytest_httpx import HTTPXMock
#
from carton.models import Players
from carton.models.poll import Poll, MultilevelPoll
from carton.providers.bgg_provider import _parse_polls, _parse_polls_summary


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
            'Best': Players(lower=4, upper=5),
            'Recommended': Players(lower=3, upper=7)
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
