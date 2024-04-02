from __future__ import annotations

from dataclasses import KW_ONLY, field
from pydantic import PositiveInt, GetCoreSchemaHandler
from pydantic.dataclasses import dataclass
from pydantic_core import core_schema
from typing import Optional, Type, Any


@dataclass(frozen=True)
class _PositiveRange:
    lower: PositiveInt
    upper: PositiveInt
    _: KW_ONLY
    unit: Optional[str] = None

    def __str__(self):
        range = f'{self.lower}-{self.upper}'
        if self.lower == self.upper:
            range = self.lower
        return f"{range}{' ' + self.unit if self.unit is not None else ''}"


@dataclass(frozen=True)
class PlayersRange(_PositiveRange):
    unit: str = field(repr=False, default='players')


@dataclass(frozen=True)
class PlayTimeRange(_PositiveRange):
    unit: str = field(repr=False, default='mins')


class MinAge(PositiveInt):
    def __str__(self):
        return f"{int(self)}+"

    def __repr__(self):
        return f"MinAge({int(self)})"

    # TODO: All this is crap
    @classmethod
    def __get_pydantic_core_schema__(cls, source: Type[Any], handler: GetCoreSchemaHandler):
        assert source is MinAge
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.int_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=core_schema.int_schema(),
            )
        )

    @staticmethod
    def _validate(value: MinAge) -> str:
        return value > 0

    @staticmethod
    def _serialize(value: MinAge) -> str:
        return value
