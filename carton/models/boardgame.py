# from __future__ import annotations
# annotations are not properly supported in current SQLAlchemy and Pydantic versions
# https://github.com/tiangolo/sqlmodel/issues/196

from sqlmodel import Field, SQLModel, Relationship

from .params import MinAge, Players, PlayTime, JSONInterval


class BoardGameDesignerLink(SQLModel, table=True):
    board_game_id: int | None = Field(default=None, foreign_key="boardgame.id", primary_key=True)
    dasigner_id: int | None = Field(default=None, foreign_key="designer.id", primary_key=True)


class BoardGame(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    designers: list['Designer'] = Relationship(back_populates="board_games", link_model=BoardGameDesignerLink)
    min_age: MinAge
    players: Players = Field(sa_type=JSONInterval)
    play_time: PlayTime = Field(sa_type=JSONInterval)
    # TODO: Add published year


# class BGGGame(BoardGame):
#     id: PositiveInt
#     community_min_age: MinAge = None
#     community_players: PlayersRange = None
#     community_best_players: PlayersRange = None


class Designer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    board_games: list[BoardGame] = Relationship(back_populates="designers", link_model=BoardGameDesignerLink)
