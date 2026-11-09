import pytest
from pydantic import ValidationError

from carton.models.boardgame import BGGGame
from carton.models.params import Players, PlayTime
from carton.models.recommendation import RecommendationCriteria, RecommendationRequest
from carton.recommender import (
    complexity_score,
    is_playable,
    players_score,
    rating_score,
    recommend,
    time_score,
)


def _game(bgg_id: int = 1, name: str = 'Game', players: list[int] | None = None,
          play_time: tuple[int, int] | None = (30, 60), **kwargs) -> BGGGame:
    return BGGGame(name=name, bgg_id=bgg_id,
                   players=Players.from_values(players or [2, 3, 4]),
                   play_time=PlayTime(lower=play_time[0], upper=play_time[1]) if play_time else None,
                   **kwargs)


def _criteria(players: int = 3, time: int = 60, complexity: float | None = None) -> RecommendationCriteria:
    return RecommendationCriteria(players=players, time=time, complexity=complexity)


@pytest.mark.parametrize('game, criteria, expected', [
    (_game(), _criteria(), True),
    (_game(players=[2, 3, 4]), _criteria(players=5), False),
    (_game(play_time=(30, 60)), _criteria(time=30), True),  # Shortest play fits
    (_game(play_time=(45, 60)), _criteria(time=30), False),
    (_game(play_time=None), _criteria(), False),
    (_game(is_expansion=True), _criteria(), False),
    # Community players are used if the publisher ones are unknown
    (BGGGame(name='Game', bgg_id=1, play_time=PlayTime(lower=30, upper=60),
             community_players=Players.from_values([3])), _criteria(), True),
    (BGGGame(name='Game', bgg_id=1, play_time=PlayTime(lower=30, upper=60)), _criteria(), False),
])
def test_is_playable(game, criteria, expected):
    assert is_playable(game, criteria) == expected


@pytest.mark.parametrize('kwargs, expected', [
    ({'community_best_players': Players.from_values([3]), 'community_players': Players.from_values([2, 3])}, 1.0),
    ({'community_best_players': Players.from_values([2]), 'community_players': Players.from_values([2, 3])}, 0.75),
    ({'community_players': Players.from_values([2])}, 0.0),
    ({}, 0.5),
])
def test_players_score(kwargs, expected):
    assert players_score(_game(**kwargs), 3) == expected


@pytest.mark.parametrize('time, expected', [(90, 1.0), (60, 1.0), (45, 0.75), (30, 0.5)])
def test_time_score(time, expected):
    assert time_score(_game(play_time=(30, 60)), time) == expected


@pytest.mark.parametrize('weight, complexity, expected', [
    (2.5, None, 1.0),
    (None, 2.5, 0.5),
    (2.5, 2.5, 1.0),
    (3.5, 2.5, 0.5),
    (1.5, 2.5, 0.5),
    (5.0, 1.0, 0.0),
])
def test_complexity_score(weight, complexity, expected):
    assert complexity_score(_game(community_average_weight=weight), complexity) == expected


@pytest.mark.parametrize('kwargs, expected', [
    ({}, 0.0),
    ({'rating': 7.0}, 0.5),
    ({'rating': 9.5, 'geek_rating': 8.0}, 0.75),  # Geek rating is preferred
    ({'geek_rating': 3.0}, 0.0),
    ({'geek_rating': 10.0}, 1.0),
])
def test_rating_score(kwargs, expected):
    assert rating_score(_game(**kwargs)) == expected


def test_recommend_sorts_and_filters():
    light = _game(1, 'Light', community_average_weight=1.5, geek_rating=7.0)
    medium = _game(2, 'Medium', community_average_weight=2.5, geek_rating=7.0)
    heavy = _game(3, 'Heavy', community_average_weight=4.0, geek_rating=8.0)
    long = _game(4, 'Long', play_time=(120, 180), community_average_weight=2.5, geek_rating=8.5)
    expansion = _game(5, 'Expansion', community_average_weight=2.5, geek_rating=8.5, is_expansion=True)

    recommendations = recommend([light, medium, heavy, long, expansion], _criteria(complexity=2.5))

    assert [r.game.name for r in recommendations] == ['Medium', 'Light', 'Heavy']
    assert recommendations[0].complexity_score == 1.0
    assert recommendations[0].score == pytest.approx(0.3 * 0.5 + 0.15 + 0.3 + 0.25 * 0.5)


def test_recommend_limit():
    games = [_game(id, f'Game {id}', geek_rating=5 + id / 10) for id in range(1, 6)]

    recommendations = recommend(games, _criteria(), limit=2)

    assert [r.game.bgg_id for r in recommendations] == [5, 4]


@pytest.mark.parametrize('request_args', [
    {'players': 0, 'time': 60, 'games': [1]},
    {'players': 2, 'time': 0, 'games': [1]},
    {'players': 2, 'time': 60, 'complexity': 6, 'games': [1]},
    {'players': 2, 'time': 60, 'games': []},
    {'players': 2, 'time': 60, 'games': [1], 'limit': 0},
])
def test_recommendation_request_invalid(request_args):
    with pytest.raises(ValidationError):
        RecommendationRequest(**request_args)
