from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from .boardgame import BGGGame
from .params import Weight

Score = Annotated[float, Field(ge=0, le=1)]


class RecommendationCriteria(BaseModel):
    """What the players are looking for in a game."""
    model_config = ConfigDict(extra="forbid")

    players: PositiveInt = Field(description="Number of players")
    time: PositiveInt = Field(description="Available time to play, in minutes")
    complexity: Weight | None = Field(
        default=None, description="Requested complexity, as BGG weight from 1 (light) to 5 (heavy), any if missing")


class RecommendationRequest(RecommendationCriteria):
    games: list[PositiveInt] = Field(min_length=1, description="BoardGameGeek ids of the games to choose from")
    limit: PositiveInt = Field(default=10, description="Maximum number of recommended games")


class Recommendation(BaseModel):
    """A recommended game, with its overall score and the score for each criterion, from 0 to 1."""
    model_config = ConfigDict(extra="forbid")

    game: BGGGame
    score: Score
    players_score: Score
    time_score: Score
    complexity_score: Score
    rating_score: Score
