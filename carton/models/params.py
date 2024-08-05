from __future__ import annotations

from pydantic import BaseModel, PositiveInt, GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Optional, Type, Any
from sqlalchemy import TypeDecorator, JSON


# TODO: Make attribute names optional
# TODO: Convert Any to generic type and add common interval methods
class Interval(BaseModel):
    lower: Any
    upper: Any
    unit: Optional[str] = None

    def __str__(self):
        interval = f'{self.lower}-{self.upper}'
        if self.lower == self.upper:
            interval = self.lower
        return f"{interval}{' ' + self.unit if self.unit is not None else ''}"


class PositiveInterval(Interval):
    lower: PositiveInt
    upper: PositiveInt
    unit: Optional[str] = None


class Players(PositiveInterval):
    unit: str = 'players'


class PlayTime(PositiveInterval):
    unit: str = 'mins'


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


# TODO: Make JSONInterval the default sa_type for all intervals
# TODO: Move this class to another place related with model persistence
class JSONInterval(TypeDecorator):
    impl = JSON

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return {'lower': value.lower, 'upper': value.upper, 'unit': value.unit}
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return PositiveInterval(lower=value['lower'], upper=value['upper'], unit=value['unit'])
        return None
