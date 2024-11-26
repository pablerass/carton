from carton.models.boardgame import BoardGame, Designer
from carton.models.params import Players, PlayTime, MinAge

# from sqlmodel import select


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
    assert designer.boardgames == {boardgame_1}

    boardgame_2 = BoardGame(
        name="Ra",
        designers=[designer],
        min_age=MinAge(12),
        players=Players(lower=2, upper=5),
        play_time=PlayTime(lower=45, upper=60),
    )

    assert boardgame_2.name == "Ra"
    assert boardgame_2.designers & boardgame_1.designers
    assert boardgame_2.min_age == MinAge(12)

    assert designer.boardgames == {boardgame_1, boardgame_2}


# def test_persistence(db_session):
#     designer = Designer(name="Reiner Knizia")
#     boardgame_1 = BoardGame(
#         name="Ra",
#         designers=[designer],
#         min_age=MinAge(10),
#         players=Players(lower=2, upper=4),
#         play_time=PlayTime(lower=45, upper=60))
#     boardgame_2 = BoardGame(
#         name="Rebirth",
#         designers=[designer],
#         min_age=MinAge(10),
#         players=Players(lower=2, upper=4),
#         play_time=PlayTime(lower=45, upper=60))
#     boardgame_3 = BoardGame(
#         name="Pelusas",
#         designers=[designer],
#         min_age=MinAge(8),
#         players=Players(lower=2, upper=5),
#         play_time=PlayTime(lower=20, upper=20))
#
#     db_session.add(boardgame_1)
#     db_session.add(boardgame_2)
#     db_session.add(boardgame_3)
#
#     db_session.commit()
#
#     designers = db_session.exec(select(Designer)).all()
#     assert len(designers) == 1
#     assert designers == [designer]
#
#     boardgames = db_session.exec(select(BoardGame)).all()
#     assert len(boardgames) == 3
#
#     simple_boardgames = db_session.exec(select(BoardGame).where(BoardGame.min_age <= 8)).all()
#     assert len(simple_boardgames) == 1
#     assert simple_boardgames[0] == boardgame_3
#
#     group_boardgames = db_session.exec(select(BoardGame).where(BoardGame.players['upper'].as_integer() >= 5)).all()
#     assert len(group_boardgames) == 1
#     assert group_boardgames[0] == boardgame_3
