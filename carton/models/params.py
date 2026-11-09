from __future__ import annotations

from collections.abc import Iterable

from pydantic import PositiveInt

from .intervals import Interval, Intervals

PlayersInterval = Interval[PositiveInt]
PlayTime = Interval[PositiveInt]
MinAge = PositiveInt
Year = PositiveInt  # TODO: Limit possible year values


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
