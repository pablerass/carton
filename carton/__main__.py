import argparse
import asyncio
import logging
import os
import sys

import pandas as pd

from .providers import BggProvider


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--bgg-user', '-u', type=str, default=os.environ.get('BGG_USER', None),
                        help='BoardGameGeek user name (or BGG_USER environment variable)')

    parser.add_argument('--bgg-password', '-p', type=str, default=os.environ.get('BGG_PASSWORD', None))
    parser.add_argument('--bgg-api-key', type=str, default=os.environ.get('BGG_API_KEY', None),
                        help='Optional BoardGameGeek API key to include on requests')

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Display verbose output")

    parsed_args = parser.parse_args(args)
    if not parsed_args.bgg_user:
        parser.error("--bgg-user or BGG_USER environment variable must be provided")
    if not parsed_args.bgg_api_key and not parsed_args.bgg_password:
        parser.error("At least one of --bgg-api-key or --bgg-password must be provided for authentication")
    if parsed_args.bgg_api_key and parsed_args.bgg_password:
        parser.error("Only one of --bgg-api-key or --bgg-password should be provided for authentication")

    return parsed_args


async def _user_collection(bgg: BggProvider, user: str):
    # Close the provider's HTTP client inside the same event loop that used it
    async with bgg:
        return await bgg.user_collection(user)


def main(args=None):
    """Execute main package command line functionality."""
    args = parse_args()

    # Logging
    if args.verbose < 3:
        logging_format = '%(levelname)s - %(message)s'
    else:
        logging_format = '[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(stream=sys.stderr, format=logging_format,
                        level=logging.WARNING - args.verbose * 10)
    if args.verbose < 4:
        logging.getLogger('httpcore').propagate = False
        logging.getLogger('httpx').propagate = False

    logger = logging.getLogger('carton.main')
    bgg = BggProvider()

    if args.bgg_api_key:
        bgg.api_login(args.bgg_api_key)
    elif args.bgg_password:
        bgg.user_login(args.bgg_user, args.bgg_password)
    else:
        logger.error("No authentication method provided")
        return 1

    user_games = asyncio.run(_user_collection(bgg, args.bgg_user))
    user_games_df = pd.DataFrame(dict(u) for u in user_games).drop('bgg_id', axis='columns')
    user_games_df['designers'] = user_games_df['designers'].apply(
        lambda x: ', '.join(str(d) for d in x))
    print(user_games_df)
    user_games_df.to_csv('~/file.csv', index=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
