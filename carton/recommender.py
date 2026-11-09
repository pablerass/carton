"""Recommend which games to play for a number of players, an available time and a complexity."""
from collections.abc import Iterable

from .models.boardgame import BGGGame
from .models.recommendation import Recommendation, RecommendationCriteria

# Weight of each criterion score in the overall score, they add up to 1
PLAYERS_WEIGHT: float = 0.3
COMPLEXITY_WEIGHT: float = 0.3
RATING_WEIGHT: float = 0.25
TIME_WEIGHT: float = 0.15

# Complexity difference, in BGG weight points, from which a game scores 0 in complexity
COMPLEXITY_TOLERANCE: float = 2.0

# Rating interval mapped to rating scores 0 to 1, as most rated games are inside it
MIN_RATING: float = 5.0
MAX_RATING: float = 9.0


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def is_playable(game: BGGGame, criteria: RecommendationCriteria) -> bool:
    """Whether the game can be played at all with the number of players and time.

    The publisher number of players is used, or the community recommended one if it is
    unknown. A game fits the time if its minimum play time does. Expansions are never
    playable on their own, see docs/adr/0001-expansions-in-recommendations.md.
    """
    if game.is_expansion:
        return False

    players = game.players or game.community_players
    if players is None or criteria.players not in players:
        return False

    return game.play_time is not None and game.play_time.lower <= criteria.time


def players_score(game: BGGGame, players: int) -> float:
    """1 if the community votes it as best with that number of players, 0.75 if recommended,
    0.5 without community votes and 0 if the community does not recommend it."""
    if game.community_best_players is not None and players in game.community_best_players:
        return 1.0
    if game.community_players is None:
        return 0.5
    if players in game.community_players:
        return 0.75
    return 0.0


def time_score(game: BGGGame, time: int) -> float:
    """1 if the longest play fits in the time, down to 0.5 if only the shortest one does."""
    if game.play_time is None:
        return 0.0
    lower, upper = game.play_time.lower, game.play_time.upper
    if upper <= time:
        return 1.0
    return _clamp(0.5 + 0.5 * (time - lower) / (upper - lower))


def complexity_score(game: BGGGame, complexity: float | None) -> float:
    """1 for the requested complexity, down to 0 at COMPLEXITY_TOLERANCE weight points of difference.

    Any game scores 1 if no complexity is requested, and 0.5 if its weight is unknown.
    """
    if complexity is None:
        return 1.0
    if game.community_average_weight is None:
        return 0.5
    return _clamp(1 - abs(game.community_average_weight - complexity) / COMPLEXITY_TOLERANCE)


def rating_score(game: BGGGame) -> float:
    """Geek rating, or average rating if missing, scaled from MIN_RATING to MAX_RATING. 0 if unrated."""
    rating = game.geek_rating or game.rating
    if rating is None:
        return 0.0
    return _clamp((rating - MIN_RATING) / (MAX_RATING - MIN_RATING))


def recommend(games: Iterable[BGGGame], criteria: RecommendationCriteria,
              limit: int | None = None) -> list[Recommendation]:
    """Return the playable games sorted from best to worst fit for the criteria.

    Games with the same score keep their original order.
    """
    recommendations = []
    for game in games:
        if not is_playable(game, criteria):
            continue

        scores = {
            'players_score': players_score(game, criteria.players),
            'time_score': time_score(game, criteria.time),
            'complexity_score': complexity_score(game, criteria.complexity),
            'rating_score': rating_score(game),
        }
        score = (PLAYERS_WEIGHT * scores['players_score'] + TIME_WEIGHT * scores['time_score']
                 + COMPLEXITY_WEIGHT * scores['complexity_score'] + RATING_WEIGHT * scores['rating_score'])
        recommendations.append(Recommendation(game=game, score=round(_clamp(score), 4), **scores))

    recommendations.sort(key=lambda recommendation: recommendation.score, reverse=True)
    return recommendations[:limit]
