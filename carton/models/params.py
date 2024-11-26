from __future__ import annotations

from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator
from typing import Sequence


# TODO: Add common interval methods
# TODO: Remove units as they are userful only for visualization and make the management more complex
class Interval[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    lower: T
    upper: T
    unit: str | None = None

    @model_validator(mode='after')
    def check_upper_and_lower(self):
        assert (self.lower <= self.upper), 'lower interval value must be lower or equal than upper'

        return self

    def __str__(self):
        interval = f'{self.lower}-{self.upper}'
        if self.lower == self.upper:
            interval = self.lower
        return f"{interval}{' ' + self.unit if self.unit is not None else ''}"

    @classmethod
    def from_list(cls, items: Sequence[PositiveInt], unit: str = None) -> Interval[PositiveInt]:
        return cls(lower=min(items), upper=max(items), unit=unit)


PositiveInterval = Interval[PositiveInt]


class Players(PositiveInterval):
    unit: str = 'players'

    @classmethod
    def from_list(cls, items: Sequence[PositiveInt], unit: str = None) -> PositiveInterval:
        return super().from_list(items, 'players')


class PlayTime(PositiveInterval):
    unit: str = 'mins'

    @classmethod
    def from_list(cls, items: Sequence[PositiveInt], unit: str = None) -> PositiveInterval:
        return super().from_list(items, 'mins')


# TODO: Add {min_age}+ as default __str__ for min_age
MinAge = PositiveInt

# TODO: Limit possible year values
Year = PositiveInt
