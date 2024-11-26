from __future__ import annotations

from pydantic import BaseModel, ConfigDict, PositiveInt

from .params import Players, PlayTime, MinAge, Year


class BoardGame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    designers: set['Designer'] = set()
    min_age: MinAge | None = None
    players: Players | None = None
    play_time: PlayTime | None = None
    published: Year | None = None
    # TODO: Add published year

    def model_post_init(self, __context):
        for d in self.designers:
            d.boardgames.add(self)

    def __hash__(self):
        return hash(self.name)


class BGGGame(BoardGame):
    bgg_id: PositiveInt
    community_min_age: MinAge | None = None
    community_players: Players | None = None
    community_best_players: Players | None = None

    def __hash__(self):
        return hash(self.bgg_id)


class Designer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    boardgames: set[BoardGame] = set()

    def __hash__(self):
        return hash(self.name)


class BGGDesigner(Designer):
    bgg_id: PositiveInt
