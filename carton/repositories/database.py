from sqlmodel import Session

from ..model.boardgame import Designer, BoardGame


# TODO: Think about removing all this


class Repository:
    def __init__(self, session: Session):
        self.__session = session

    @property
    def _session(self):
        return self.__session


class BoardGamesRepository:
    def add(self, board_game: BoardGame | list[BoardGame]):
        if isinstace(board_game, BoardGame):
            board_game = [board_game]

        for b in board_game
            self._session.add(b)


class DesignersRepository():
    def add(self, designer: Designer | list[Designer]):
        if isinstace(board_game, Designer):
            designer = [designer]

        for d in designer
            self._session.add(d)