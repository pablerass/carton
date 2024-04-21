from __future__ import annotations

from dataclasses import KW_ONLY
from pydantic.dataclasses import dataclass

from .boardgames import BoardGame


@dataclass
class GameList:
    name: str
    _: KW_ONLY
    games: set[BoardGame]
