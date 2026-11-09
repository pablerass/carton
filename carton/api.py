import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx2
from fastapi import Depends, FastAPI, HTTPException, Request

from . import __version__
from .auth import bgg_login
from .cache import default_cache_file, load_cache, save_cache
from .models.boardgame import BGGGame
from .providers import BggProvider, BggUserNotFoundError


async def _authenticate(bgg: BggProvider) -> None:
    """Authenticate the provider with BGG_API_KEY, or BGG_USER and BGG_PASSWORD."""
    try:
        # Password login is blocking, so it is run outside the event loop
        await asyncio.to_thread(bgg_login, bgg, api_key=os.environ.get('BGG_API_KEY'),
                                user=os.environ.get('BGG_USER'), password=os.environ.get('BGG_PASSWORD'))
    except ValueError as error:
        raise RuntimeError(f"Invalid BGG_API_KEY, BGG_USER and BGG_PASSWORD configuration: {error}") from error


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # A single provider is shared by all requests, so they reuse its connection pool and cache
    cache_file = default_cache_file()
    cache = load_cache(cache_file)
    async with BggProvider(return_cache=cache) as bgg:
        await _authenticate(bgg)
        app.state.bgg = bgg
        try:
            yield
        finally:
            save_cache(cache, cache_file)


# Run with: uvicorn carton.api:app
# Every endpoint should have an equivalent CLI command, see docs/adr/0002-cli-and-api-parity.md
app = FastAPI(title="Carton", version=__version__, lifespan=lifespan)


def get_bgg(request: Request) -> BggProvider:
    return request.app.state.bgg


# TUNE: Instead of list of BGGGame this should return a list of BoardGames
@app.get("/users/{username}/collection", response_model=list[BGGGame])
async def user_collection(username: str, bgg: Annotated[BggProvider, Depends(get_bgg)]) -> list[BGGGame]:
    """Return all games and expansions owned by a BoardGameGeek user."""
    logger = logging.getLogger('carton.api.user_collection')

    try:
        return await bgg.user_collection(username)
    except BggUserNotFoundError:
        raise HTTPException(status_code=404, detail=f"BoardGameGeek user '{username}' not found")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="BoardGameGeek kept the request queued, try again later")
    except httpx2.HTTPError as error:
        logger.error(f"Error obtaining {username} collection from BoardGameGeek: {error}")
        raise HTTPException(status_code=502, detail="Error obtaining the collection from BoardGameGeek")
