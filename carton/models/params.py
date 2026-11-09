from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated

from pydantic import Field, PositiveInt

from .intervals import Interval, Intervals

PlayersInterval = Interval[PositiveInt]
PlayTime = Interval[PositiveInt]
MinAge = PositiveInt
Year = PositiveInt  # TODO: Limit possible year values
Rating = Annotated[float, Field(ge=1, le=10)]
Weight = Annotated[float, Field(ge=1, le=5)]  # BGG complexity, from 1 (light) to 5 (heavy)
Rank = PositiveInt


class Players(Intervals[PositiveInt]):
    @classmethod
    def from_values(cls, values: Iterable[int]) -> Players:
        """Build Players grouping consecutive numbers of players in the same interval."""
        groups: list[list[int]] = []
        for value in sorted(set(values)):
            if groups and value == groups[-1][-1] + 1:
                groups[-1].append(value)
            else:
                groups.append([value])

        return cls.from_list(groups)
