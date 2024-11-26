import argparse
import asyncio
import logging
import os
import pandas as pd
import sys

from .providers import BggProvider


def parse_args(args: list[str] = None) -> argparse.Namespace:
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--trello-api-key', type=str, default=os.environ.get('TRELLO_API_KEY', None))
    parser.add_argument('--trello-api-token', type=str, default=os.environ.get('TRELLO_API_TOKEN', None))
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Display verbose output")

    return parser.parse_args(args)


async def main(args=None):
    """Execute main package command line functionality."""
    args = parse_args()

    # Logging
    if args.verbose < 3:
        logging_format = '%(levelname)s - %(message)s'
    else:
        logging_format = '[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(stream=sys.stderr, format=logging_format,
                        level=logging.WARN - args.verbose * 10)
    if args.verbose < 4:
        logging.getLogger('httpcore').propagate = False
        logging.getLogger('httpx').propagate = False

    # trello = TrelloProvider(args.trello_api_key, args.trello_api_token)
    # boardgame_names = [
    #     card['name'] for card in
    #     await trello.list_cards('5fe62b9d8934f35ed591137a')]
    # boardgames = await aiometer.run_all(
    #     [partial(bgg.boardgame_by_name, name) for name in boardgame_names[:3]],
    #     max_at_once=8,
    #     max_per_second=5
    # )
    # print(boardgames)

    user_games = await BggProvider().user_collection('pablerzas')
    user_games_df = pd.DataFrame(dict(u) for u in user_games)
    user_games_df.to_csv('~/file.csv')


    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
