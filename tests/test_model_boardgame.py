from carton.models.boardgame import BoardGame, Designer
from carton.models.params import MinAge, Players, PlayTime

from sqlmodel import select


def test_board_game():
    designer = Designer(name="Reiner Knizia")

    boardgame_1 = BoardGame(
        name="Rebirth",
        designers=[designer],
        min_age=MinAge(10),
        players=Players(lower=2, upper=4),
        play_time=PlayTime(lower=45, upper=60)
    )

    assert boardgame_1.name == "Rebirth"
    assert designer.board_games == [boardgame_1]

    boardgame_2 = BoardGame(
        name="Ra",
        designers=[designer],
        min_age=MinAge(12),
        players=Players(lower=2, upper=5),
        play_time=PlayTime(lower=45, upper=60),
    )

    assert boardgame_2.name == "Ra"
    assert boardgame_2.designers[0] == boardgame_1.designers[0]
    assert boardgame_2.min_age == MinAge(12)

    assert designer.board_games == [boardgame_1, boardgame_2]


def test_persistence(db_session):
    boardgame_1 = BoardGame(
        name="Ra",
        designers=[Designer(name="Reiner Knizia")],
        min_age=MinAge(10),
        players=Players(lower=2, upper=4),
        play_time=PlayTime(lower=45, upper=60))
    boardgame_2 = BoardGame(
        name="Rebirth",
        designers=[Designer(name="Reiner Knizia")],
        min_age=MinAge(10),
        players=Players(lower=2, upper=4),
        play_time=PlayTime(lower=45, upper=60))
    boardgame_3 = BoardGame(
        name="Pelusas",
        designers=[Designer(name="Reiner Knizia")],
        min_age=MinAge(8),
        players=Players(lower=2, upper=5),
        play_time=PlayTime(lower=20, upper=20))

    db_session.add(boardgame_1)
    db_session.add(boardgame_2)
    db_session.add(boardgame_3)

    db_session.commit()

    boardgames = db_session.exec(select(BoardGame)).all()
    assert len(boardgames) == 3
