# from __future__ import annotations
# annotations are not properly supported in current SQLAlchemy and Pydantic versions
# https://github.com/tiangolo/sqlmodel/issues/196

from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    board_games: list[BoardGame] = Relationship


class Club(SQLModel, table=True):
    pass


class SessionBoardGameVotes(SQLModel, table=True):
    user: 'User' = Relationship()
    session: str


class SessionBoardGames(SQLModel, table=True):
    session: str | None = Field(default=None, foreign_key="session.id", primary_key=True)
    board_game: int | None = Field(default=None, foreign_key="boardgame.id", primary_key=True)
    users_voted: list[User] = Relationship(link_model=SessionBoardGameVotes)


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    creator: 'User' = Relationship()
    available_games: list[BoardGame] = Relationship
    open: bool = Filed(default=False)