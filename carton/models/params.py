from __future__ import annotations

from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator
from typing import Sequence


# TODO: Add common interval methods such as join, etc.
class Interval[T](BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lower: T
    upper: T

    @model_validator(mode='after')
    def check_upper_and_lower(self):
        assert (self.lower <= self.upper), 'lower interval value must be lower or equal than upper'

        return self

    def __str__(self):
        interval = f'{self.lower}-{self.upper}'
        if self.lower == self.upper:
            interval = str(self.lower)
        return interval

    @classmethod
    def from_list(cls, items: Sequence[T]) -> Interval[T]:
        print(items)
        return cls(lower=min(items), upper=max(items))


class Intervals[T](BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # TUNE: Maybe this could use nargs instead of a list as parameter
    intervals: list[T]

    def __str__(self):
        return ', '.join([str(interval) for interval in self.intervals])

    @classmethod
    def from_list(cls, items: Sequence[Sequence[T]]) -> Intervals[T]:
        return cls(intervals=[
            Interval[T].from_list(interval_items) for interval_items in items])


PlayersInterval = Interval[PositiveInt]
Players = Intervals[PlayersInterval]
PlayTime = Interval[PositiveInt]
MinAge = PositiveInt
Year = PositiveInt  # TODO: Limit possible year values
