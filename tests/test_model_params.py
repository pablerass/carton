import pytest

from pydantic import ValidationError

from carton.models.params import _PositiveRange, PlayersRange, PlayTimeRange, MinAge


def test_range():
    assert str(_PositiveRange(1, 4)) == '1-4'

    assert str(_PositiveRange(1, 4, unit='tomatos')) == '1-4 tomatos'

    with pytest.raises(ValidationError):
        _PositiveRange(1, 4, 'beers')

    with pytest.raises(ValidationError):
        _PositiveRange(0, 4, 'beers')


def test_player_range():
    assert str(PlayersRange(1, 4)) == '1-4 players'

    assert str(PlayersRange(1, 4, unit='beets')) == '1-4 beets'


def test_play_time_range():
    assert str(PlayTimeRange(30, 240)) == '30-240 mins'


def test_min_int():
    assert str(MinAge(1)) == '1+'
