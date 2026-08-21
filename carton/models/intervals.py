from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from pydantic import BaseModel, ConfigDict, model_validator


@runtime_checkable
class Orderable(Protocol):
    def __lt__(self, other: object, /) -> bool: ...
    def __le__(self, other: object, /) -> bool: ...
    def __gt__(self, other: object, /) -> bool: ...
    def __ge__(self, other: object, /) -> bool: ...


class Interval[T: Orderable](BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, arbitrary_types_allowed=True)

    lower: T
    upper: T

    @model_validator(mode="after")
    def validate_order(self):
        try:
            valid = self.lower <= self.upper
        except TypeError as error:
            raise ValueError("interval values must be orderable") from error

        if not valid:
            raise ValueError("lower must be less than or equal to upper")

        return self

    def __contains__(self, item: T) -> bool:
        return self.lower <= item <= self.upper

    def __str__(self):
        interval = f'{self.lower}-{self.upper}'
        if self.lower == self.upper:
            interval = str(self.lower)
        return interval

    @classmethod
    def from_list(cls, items: Sequence[T]) -> Interval[T]:
        return cls(lower=min(items), upper=max(items))


class Intervals[T: Orderable](BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, arbitrary_types_allowed=True)

    intervals: list[Interval[T]]

    def __contains__(self, item: T) -> bool:
        return any(item in interval for interval in self.intervals)

    def __str__(self):
        return ', '.join([str(interval) for interval in self.intervals])

    @classmethod
    def from_list(cls, items: Sequence[Sequence[T]]) -> Intervals[T]:
        return cls(intervals=[Interval.from_list(interval_items) for interval_items in items])
