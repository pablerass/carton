from __future__ import annotations

from pydantic import BaseModel, ConfigDict, NonNegativeInt, PositiveInt

from .params import MinAge, Players, PlayTime, Rank, Rating, Year


class BoardGame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    designers: set[Designer] = set()
    min_age: MinAge | None = None
    players: Players | None = None
    play_time: PlayTime | None = None
    published: Year | None = None
    is_expansion: bool = False
    # TODO: Add expansions relation, see docs/adr/0001-expansions-in-recommendations.md

    def model_post_init(self, context, /):
        for d in self.designers:
            d.boardgames.add(self)

    def __hash__(self):
        return hash(self.name)


class BGGGame(BoardGame):
    bgg_id: PositiveInt
    community_min_age: MinAge | None = None
    community_players: Players | None = None
    community_best_players: Players | None = None
    community_average_weight: float | None = None
    rating: Rating | None = None  # Average users rating
    geek_rating: Rating | None = None  # Bayesian average rating used for ranking
    num_ratings: NonNegativeInt | None = None
    rank: Rank | None = None  # Overall Board Game Rank

    def __hash__(self):
        return hash(self.bgg_id)


class Designer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    boardgames: set[BoardGame] = set()

    def __str__(self) -> str:
        return self.name

    def __hash__(self):
        return hash(self.name)


class BGGDesigner(Designer):
    bgg_id: PositiveInt
