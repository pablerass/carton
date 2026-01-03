import pytest

from pydantic import ValidationError

from carton.models.params import Interval, PositiveInt, PlayersInterval, Players, PlayTime, MinAge


def test_intervals():
    with pytest.raises(ValidationError):
        Interval[PositiveInt](lower=0, upper=4)

    with pytest.raises(ValidationError):
        Interval[int](lower=5, upper=1)

    assert str(Interval[PositiveInt](lower=1, upper=4)) == '1-4'
    assert str(Interval[PositiveInt].from_list([1, 3, 4, 6])) == '1-6'


def test_players():
    players_interval = PlayersInterval(lower=1, upper=4)
    assert str(players_interval) == '1-4'
    assert str(Players(intervals=[players_interval])) == '1-4'

    assert str(Players.from_list([[1, 4, 3]])) == '1-4'
    assert str(Players.from_list([[1, 2], [4]])) == '1-2, 4'


def test_play_time():
    assert str(PlayTime(lower=30, upper=240)) == '30-240'


def test_min_int():
    assert str(MinAge(1)) == '1'
