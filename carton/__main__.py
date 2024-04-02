import argparse
import asyncio
import logging
import sys

from .providers import BggProvider


def parse_args(args: list[str] = None) -> argparse.Namespace:
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Display verbose output")

    return parser.parse_args(args)


def main(args=None):
    """Execute main package command line functionality."""
    args = parse_args()

    # Logging
    if args.verbose < 3:
        logging_format = '%(levelname)s - %(message)s'
    else:
        logging_format = '[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(stream=sys.stderr, format=logging_format,
                        level=logging.WARN - args.verbose * 10)

    boardgame = asyncio.run(BggProvider().boardgame_by_name('Catan'))
    print(boardgame)

    return 0


if __name__ == "__main__":
    sys.exit(main())
