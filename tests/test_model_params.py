import pytest

from pydantic import ValidationError

from carton.models.params import PositiveInterval, Players, PlayTime, MinAge


def test_intervals():
    assert str(PositiveInterval(lower=1, upper=4)) == '1-4'

    assert str(PositiveInterval(lower=1, upper=4, unit='tomatos')) == '1-4 tomatos'

    with pytest.raises(ValidationError):
        PositiveInterval(lower=0, upper=4, units='beers')


def test_players():
    assert str(Players(lower=1, upper=4)) == '1-4 players'

    assert str(Players(lower=1, upper=4, unit='beets')) == '1-4 beets'


def test_play_time():
    assert str(PlayTime(lower=30, upper=240)) == '30-240 mins'


def test_min_int():
    assert str(MinAge(1)) == '1+'
