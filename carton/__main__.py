import argparse
import asyncio
import csv
import logging
import os
import sys
from typing import TextIO

from pydantic import BaseModel, TypeAdapter

from .auth import bgg_login
from .cache import default_cache_file, load_cache, save_cache
from .models.boardgame import BGGGame
from .providers import BggProvider, BggUserNotFoundError

OUTPUT_FORMATS = ('csv', 'json')


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    if args is None:
        args = sys.argv[1:]

    # Every API endpoint should have an equivalent command, see docs/adr/0002-cli-and-api-parity.md
    parser = argparse.ArgumentParser(description='Manage board gaming sessions with BoardGameGeek data')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Display verbose output")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Collection export
    collection_parser = subparsers.add_parser(
        'collection', help='Export a user collection',
        description='Export all games and expansions owned by a BoardGameGeek user.')
    collection_parser.add_argument('user', nargs='?',
                                   help='User whose collection is exported (default: --bgg-user)')
    collection_parser.add_argument('--bgg-user', '-u', type=str, default=os.environ.get('BGG_USER'),
                                   help='BoardGameGeek user name (or BGG_USER environment variable)')
    collection_parser.add_argument('--bgg-password', '-p', type=str, default=os.environ.get('BGG_PASSWORD'),
                                   help='BoardGameGeek password (or BGG_PASSWORD environment variable)')
    collection_parser.add_argument('--bgg-api-key', type=str, default=os.environ.get('BGG_API_KEY'),
                                   help='BoardGameGeek API key (or BGG_API_KEY environment variable)')
    collection_parser.add_argument('--format', '-f', choices=OUTPUT_FORMATS, default='csv',
                                   help='Output format (default: csv)')
    collection_parser.add_argument('--output', '-o', type=str, default='-',
                                   help='File to write the collection to (default: standard output)')
    collection_parser.add_argument('--cache-file', type=str, default=str(default_cache_file()),
                                   help='File where BoardGameGeek games are cached '
                                        '(or CARTON_CACHE_FILE environment variable, default: %(default)s)')
    collection_parser.add_argument('--no-cache', action='store_true',
                                   help='Request every game to BoardGameGeek without reading or updating the cache')

    parsed_args = parser.parse_args(args)

    if parsed_args.command == 'collection':
        if not parsed_args.bgg_api_key and not parsed_args.bgg_password:
            collection_parser.error("At least one of --bgg-api-key or --bgg-password must be provided "
                                    "for authentication")
        if parsed_args.bgg_api_key and parsed_args.bgg_password:
            collection_parser.error("Only one of --bgg-api-key or --bgg-password should be provided "
                                    "for authentication")
        if parsed_args.bgg_password and not parsed_args.bgg_user:
            collection_parser.error("--bgg-user or BGG_USER environment variable must be provided "
                                    "to authenticate with a password")
        parsed_args.user = parsed_args.user or parsed_args.bgg_user
        if not parsed_args.user:
            collection_parser.error("A user, --bgg-user or BGG_USER environment variable must be provided")

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


async def _user_collection(bgg: BggProvider, user: str) -> list[BGGGame]:
    # Close the provider's HTTP client inside the same event loop that used it
    async with bgg:
        return await bgg.user_collection(user)


def collection(args: argparse.Namespace) -> int:
    logger = logging.getLogger('carton.main.collection')

    cache = None if args.no_cache else load_cache(args.cache_file)
    bgg = BggProvider(return_cache=cache)
    bgg_login(bgg, api_key=args.bgg_api_key, user=args.bgg_user, password=args.bgg_password)

    try:
        games = asyncio.run(_user_collection(bgg, args.user))
    except BggUserNotFoundError:
        logger.error(f"BoardGameGeek user '{args.user}' not found")
        return 1
    finally:
        # Games obtained before a failure are kept too
        if cache is not None:
            save_cache(cache, args.cache_file)

    if args.output == '-':
        write_collection(games, sys.stdout, args.format)
    else:
        with open(args.output, 'w', newline='') as output:
            write_collection(games, output, args.format)

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
        logging.getLogger('httpcore').propagate = False
        logging.getLogger('httpx').propagate = False

    match parsed_args.command:
        case 'collection':
            return collection(parsed_args)
        case _:
            raise ValueError(f"Unknown command {parsed_args.command}")


if __name__ == "__main__":
    sys.exit(main())
