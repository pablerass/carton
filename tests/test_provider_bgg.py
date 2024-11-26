# import pytest
# 
# from pytest_httpx import HTTPXMock
# 
# from carton.providers.bgg_provider import BggProvider
# 
# 
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