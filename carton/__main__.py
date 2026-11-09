import argparse
import asyncio
import csv
import io
import json
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from typing import TextIO

from pydantic import BaseModel, TypeAdapter, ValidationError

from .auth import bgg_login
from .cache import default_cache_file, load_cache, save_cache
from .models.boardgame import BGGGame
from .models.recommendation import Recommendation, RecommendationCriteria
from .providers import BggGameNotFoundError, BggProvider, BggUserNotFoundError
from .recommender import recommend

OUTPUT_FORMATS = ('csv', 'json')


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    if args is None:
        args = sys.argv[1:]

    # Every API endpoint should have an equivalent command, see docs/adr/0002-cli-and-api-parity.md
    parser = argparse.ArgumentParser(description='Manage board gaming sessions with BoardGameGeek data')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Display verbose output")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Options shared by all commands
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--bgg-user', '-u', type=str, default=os.environ.get('BGG_USER'),
                               help='BoardGameGeek user name (or BGG_USER environment variable)')
    common_parser.add_argument('--bgg-password', '-p', type=str, default=os.environ.get('BGG_PASSWORD'),
                               help='BoardGameGeek password (or BGG_PASSWORD environment variable)')
    common_parser.add_argument('--bgg-api-key', type=str, default=os.environ.get('BGG_API_KEY'),
                               help='BoardGameGeek API key (or BGG_API_KEY environment variable)')
    common_parser.add_argument('--format', '-f', choices=OUTPUT_FORMATS, default='csv',
                               help='Output format (default: csv)')
    common_parser.add_argument('--output', '-o', type=str, default='-',
                               help='File to write the result to (default: standard output)')
    common_parser.add_argument('--cache-file', type=str, default=str(default_cache_file()),
                               help='File where BoardGameGeek games are cached '
                                    '(or CARTON_CACHE_FILE environment variable, default: %(default)s)')
    common_parser.add_argument('--no-cache', action='store_true',
                               help='Request every game to BoardGameGeek without reading or updating the cache')

    # Collection export
    collection_parser = subparsers.add_parser(
        'collection', parents=[common_parser], help='Export a user collection',
        description='Export all games and expansions owned by a BoardGameGeek user.')
    collection_parser.add_argument('user', nargs='?',
                                   help='User whose collection is exported (default: --bgg-user)')

    # Recommendation
    recommend_parser = subparsers.add_parser(
        'recommend', parents=[common_parser], help='Recommend the best games to play',
        description='Recommend the best games to play, from a file of BoardGameGeek ids or from the '
                    'collection of a BoardGameGeek user, best first. Expansions and games that '
                    "can't be played with the number of players or in the time are not recommended.")
    recommend_parser.add_argument('user', nargs='?',
                                  help='User whose collection games are recommended '
                                       '(default: --bgg-user, unless --games-file is provided)')
    recommend_parser.add_argument('--games-file', '-g', type=str,
                                  help='File with the BoardGameGeek ids of the games to recommend: one id per '
                                       "line, or the CSV or JSON written by the 'collection' command "
                                       "('-' for standard input)")
    recommend_parser.add_argument('--players', '-n', type=int, required=True, help='Number of players')
    recommend_parser.add_argument('--time', '-t', type=int, required=True,
                                  help='Available time to play, in minutes')
    recommend_parser.add_argument('--complexity', '-c', type=float,
                                  help='Requested complexity, as BGG weight from 1 (light) to 5 (heavy) '
                                       '(default: any)')
    recommend_parser.add_argument('--limit', '-l', type=int, default=10,
                                  help='Maximum number of recommended games (default: %(default)s)')

    parsed_args = parser.parse_args(args)
    command_parser = {'collection': collection_parser, 'recommend': recommend_parser}[parsed_args.command]

    if not parsed_args.bgg_api_key and not parsed_args.bgg_password:
        command_parser.error("At least one of --bgg-api-key or --bgg-password must be provided "
                             "for authentication")
    if parsed_args.bgg_api_key and parsed_args.bgg_password:
        command_parser.error("Only one of --bgg-api-key or --bgg-password should be provided "
                             "for authentication")
    if parsed_args.bgg_password and not parsed_args.bgg_user:
        command_parser.error("--bgg-user or BGG_USER environment variable must be provided "
                             "to authenticate with a password")

    if parsed_args.command == 'recommend':
        if parsed_args.games_file and parsed_args.user:
            command_parser.error("Only one of a user or --games-file should be provided")
        try:
            RecommendationCriteria(players=parsed_args.players, time=parsed_args.time,
                                   complexity=parsed_args.complexity)
        except ValidationError as error:
            command_parser.error(f"Invalid recommendation criteria: {error}")
        if parsed_args.limit < 1:
            command_parser.error("--limit must be a positive number")

    if parsed_args.command == 'collection' or not parsed_args.games_file:
        parsed_args.user = parsed_args.user or parsed_args.bgg_user
        if not parsed_args.user:
            games_file = ', or --games-file' if parsed_args.command == 'recommend' else ''
            command_parser.error(f"A user, --bgg-user or BGG_USER environment variable{games_file} must be provided")

    return parsed_args


def _csv_value(value) -> str | int | float | bool | None:
    """Flatten a game field value into a single CSV cell."""
    if isinstance(value, set | list):
        return ', '.join(sorted(str(v) for v in value))
    if isinstance(value, BaseModel):
        return str(value)
    return value


def write_collection(games: list[BGGGame], output: TextIO, output_format: str = 'csv') -> None:
    if output_format == 'json':
        output.write(TypeAdapter(list[BGGGame]).dump_json(games, indent=2).decode())
        output.write('\n')
        return

    writer = csv.DictWriter(output, fieldnames=list(BGGGame.model_fields))
    writer.writeheader()
    for game in games:
        writer.writerow({field: _csv_value(getattr(game, field)) for field in BGGGame.model_fields})


def write_recommendations(recommendations: list[Recommendation], output: TextIO,
                          output_format: str = 'csv') -> None:
    if output_format == 'json':
        output.write(TypeAdapter(list[Recommendation]).dump_json(recommendations, indent=2).decode())
        output.write('\n')
        return

    score_fields = [field for field in Recommendation.model_fields if field != 'game']
    writer = csv.DictWriter(output, fieldnames=score_fields + list(BGGGame.model_fields))
    writer.writeheader()
    for recommendation in recommendations:
        writer.writerow({field: getattr(recommendation, field) for field in score_fields}
                        | {field: _csv_value(getattr(recommendation.game, field)) for field in BGGGame.model_fields})


def read_game_ids(games_file: TextIO) -> list[int]:
    """Read BoardGameGeek ids from a file with one id per line, or a CSV or JSON written by 'collection'.

    Blank lines and lines starting with '#' are ignored in id per line files. JSON files
    may contain a list of ids or a list of games.
    """
    content = games_file.read()
    stripped = content.lstrip()

    if stripped.startswith('['):
        return [int(item['bgg_id'] if isinstance(item, dict) else item) for item in json.loads(content)]

    lines = [line.strip() for line in content.splitlines()]
    lines = [line for line in lines if line and not line.startswith('#')]
    if lines and 'bgg_id' in next(csv.reader([lines[0]])):
        return [int(row['bgg_id']) for row in csv.DictReader(io.StringIO(content))]

    return [int(line) for line in lines]


def _run_bgg[T](args: argparse.Namespace, operation: Callable[[BggProvider], Awaitable[T]]) -> T:
    """Run an operation with an authenticated provider, using and updating the cache."""
    cache = None if args.no_cache else load_cache(args.cache_file)
    bgg = BggProvider(return_cache=cache)
    bgg_login(bgg, api_key=args.bgg_api_key, user=args.bgg_user, password=args.bgg_password)

    async def run() -> T:
        # Close the provider's HTTP client inside the same event loop that used it
        async with bgg:
            return await operation(bgg)

    try:
        return asyncio.run(run())
    finally:
        # Games obtained before a failure are kept too
        if cache is not None:
            save_cache(cache, args.cache_file)


def _write_output[T](args: argparse.Namespace, writer: Callable[[T, TextIO, str], None], result: T) -> None:
    if args.output == '-':
        writer(result, sys.stdout, args.format)
    else:
        with open(args.output, 'w', newline='') as output:
            writer(result, output, args.format)


def collection(args: argparse.Namespace) -> int:
    logger = logging.getLogger('carton.main.collection')

    try:
        games = _run_bgg(args, lambda bgg: bgg.user_collection(args.user))
    except BggUserNotFoundError:
        logger.error(f"BoardGameGeek user '{args.user}' not found")
        return 1

    _write_output(args, write_collection, games)
    return 0


def recommend_games(args: argparse.Namespace) -> int:
    logger = logging.getLogger('carton.main.recommend')

    criteria = RecommendationCriteria(players=args.players, time=args.time, complexity=args.complexity)

    if args.games_file:
        try:
            if args.games_file == '-':
                game_ids = read_game_ids(sys.stdin)
            else:
                with open(args.games_file, newline='') as games_file:
                    game_ids = read_game_ids(games_file)
        except (OSError, ValueError, KeyError, TypeError) as error:
            logger.error(f"Unable to read BoardGameGeek ids from {args.games_file}: {error!r}")
            return 1
        if not game_ids:
            logger.error(f"No BoardGameGeek ids found in {args.games_file}")
            return 1

    async def games(bgg: BggProvider) -> list[BGGGame]:
        if args.games_file:
            return await bgg.boardgames_by_id(game_ids)
        return await bgg.user_collection(args.user)

    try:
        recommendations = recommend(_run_bgg(args, games), criteria, limit=args.limit)
    except BggUserNotFoundError:
        logger.error(f"BoardGameGeek user '{args.user}' not found")
        return 1
    except BggGameNotFoundError as error:
        logger.error(str(error))
        return 1

    _write_output(args, write_recommendations, recommendations)
    return 0


def main(args: list[str] | None = None) -> int:
    """Execute main package command line functionality."""
    parsed_args = parse_args(args)

    # Logging
    if parsed_args.verbose < 3:
        logging_format = '%(levelname)s - %(message)s'
    else:
        logging_format = '[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(stream=sys.stderr, format=logging_format,
                        level=logging.WARNING - parsed_args.verbose * 10)
    if parsed_args.verbose < 4:
        logging.getLogger('httpcore2').propagate = False
        logging.getLogger('httpx2').propagate = False

    match parsed_args.command:
        case 'collection':
            return collection(parsed_args)
        case 'recommend':
            return recommend_games(parsed_args)
        case _:
            raise ValueError(f"Unknown command {parsed_args.command}")


if __name__ == "__main__":
    sys.exit(main())
