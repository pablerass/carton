from __future__ import annotations

from dataclasses import KW_ONLY
from pydantic import PositiveInt
from pydantic.dataclasses import dataclass

from .params import MinAge, PlayersRange, PlayTimeRange


@dataclass(frozen=True)
class BoardGame:
    name: str
    _: KW_ONLY
    # TODO: Allow múltiple designer
    designer: Designer
    min_age: MinAge
    players: PlayersRange
    play_time: PlayTimeRange
    # TODO: Add published year

    def __post_init__(self):
        # TUNE: This is not a good idea
        self.designer.add_game(self)


@dataclass(frozen=True)
class BGGGame(BoardGame):
    id: PositiveInt
    community_min_age: MinAge = None
    community_players: PlayersRange = None
    community_best_players: PlayersRange = None


@dataclass
class Designer:
    name: str
    _: KW_ONLY
    games: set[BoardGame] = None

    def __post_init__(self):
        if self.games is None:
            self.games = set()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_game(self, game: BoardGame):
        self.games |= set([game])
