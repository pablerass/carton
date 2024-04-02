from carton.models.boardgame import BoardGame, BGGGame, Designer
from carton.models.params import MinAge, PlayersRange, PlayTimeRange


def test_boardgame():
    designer = Designer("Reiner Knizia")

    boardgame_1 = BoardGame(
        "Rebirth",
        designer=designer,
        min_age=MinAge(10),
        players=PlayersRange(2, 4),
        play_time=PlayTimeRange(45, 60)
    )

    assert boardgame_1.name == "Rebirth"
    assert designer.games == set([boardgame_1])

    boardgame_2 = BGGGame(
        "Ra",
        designer=designer,
        min_age=MinAge(12),
        players=PlayersRange(2, 5),
        play_time=PlayTimeRange(45, 60),
        community_min_age=MinAge(10),
        community_players=PlayersRange(2, 5),
        community_best_player=PlayersRange(3, 4),
        id=12
    )

    assert boardgame_2.id == 12
    assert boardgame_2.name == "Ra"
    assert boardgame_2.designer == boardgame_1.designer

    assert designer.games == set([boardgame_1, boardgame_2])
