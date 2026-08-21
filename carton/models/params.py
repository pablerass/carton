from __future__ import annotations

from pydantic import PositiveInt

from .intervals import Interval, Intervals


PlayersInterval = Interval[PositiveInt]
Players = Intervals[PositiveInt]
PlayTime = Interval[PositiveInt]
MinAge = PositiveInt
Year = PositiveInt  # TODO: Limit possible year values
