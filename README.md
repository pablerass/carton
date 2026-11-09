# Carton

An attempt to create a service to manage board gaming sessions.

![Powered by BoardGameGeek](docs/assets/powered-by-bgg-rgb.svg)

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/)

## Installation

Clone the repository and install the project with its dependencies:

```sh
uv sync
```

This creates a virtual environment in `.venv` with the package and the `dev`
and `test` dependency groups installed. To install only the runtime
dependencies, use `uv sync --no-default-groups`.

## Usage

Carton can be used as a command line tool or as an API. Every API endpoint has
an equivalent command, see
[ADR 2](docs/adr/0002-cli-and-api-parity.md).

Both authenticate against BoardGameGeek with an API key, or with a user and a
password, provided via the `BGG_API_KEY`, or `BGG_USER` and `BGG_PASSWORD`,
environment variables.

### Command line

The project exposes a `carton` command:

```sh
uv run carton collection <user> --bgg-api-key <api-key>
# or
uv run carton collection <user> --bgg-user <login-user> --bgg-password <password>
```

If `<user>` is omitted, the collection of `--bgg-user` is exported. The
collection is written as CSV to standard output. Use `--format json` to get
JSON and `--output <file>` to write it to a file. Run `uv run carton --help` or
`uv run carton <command> --help` for all options.

To get the best games to play for a number of players, an available time in
minutes and an optional complexity (BGG weight, from 1 to 5), from the
collection of a user or from a file of BGG ids:

```sh
uv run carton recommend <user> --players 4 --time 90 --complexity 2.5
uv run carton recommend --games-file games.txt --players 4 --time 90
```

The games file contains one BGG id per line, or is a CSV or JSON written by
`carton collection`. Games are scored from 0 to 1, best first, by how well they
play with that number of players according to the BGG community, how well they
fit the time, how close their weight is to the requested complexity and their
BGG rating. Expansions, and games that can't be played with that number of
players or in that time, are not recommended. Use `--limit` to change the
number of games returned (10 by default).

To install the command globally as a tool:

```sh
uv tool install .
carton --help
```

### API

The API is the ASGI application `carton.api:app`, run it with
[uvicorn](https://www.uvicorn.org/):

```sh
BGG_API_KEY=<api-key> uv run uvicorn carton.api:app --reload
```

Endpoints:

| Endpoint                         | Command                       | Description                                       |
|----------------------------------|-------------------------------|---------------------------------------------------|
| `GET /users/{username}/collection` | `carton collection <username>` | All games and expansions owned by a BGG user, 404 if the user does not exist |
| `POST /recommend`                | `carton recommend --games-file <file>` | Best games to play from a list of BGG ids, 404 if any game does not exist |

`POST /recommend` receives a JSON body such as
`{"players": 4, "time": 90, "complexity": 2.5, "games": [13, 822, 230802], "limit": 10}`,
where `complexity` and `limit` are optional.

Interactive documentation is available at `http://127.0.0.1:8000/docs`.

## Cache

Games obtained from BoardGameGeek are cached with
[cartucho](https://github.com/pablerass/cartucho) in a local file, so they are
not requested again. Collections are always requested, so newly owned games
are found. Delete the cache file to obtain updated game data.

| Variable            | Default                      | Description                                 |
|---------------------|------------------------------|---------------------------------------------|
| `CARTON_CACHE_FILE` | `~/.cache/carton/bgg.pickle` | File where games are cached                 |

The CLI also accepts `--cache-file` and `--no-cache`. The API
loads the cache on startup and saves it on shutdown. The cache file is
unpickled when loaded, so it must only be writable by trusted users.

## Docker

The Docker image runs the API. Copy the example environment file and fill in
your BoardGameGeek credentials:

```sh
cp .env.example .env
```

Then build and start the server:

```sh
docker compose up --build
```

The API is published on port 8000 of the host, set `CARTON_PORT` to use a
different one.

cartucho is installed from `../cartucho`, so it has to be checked out next to
this repository. The cache is kept in the `cache` volume.

## Development

```sh
make lint           # ruff
make type-check     # ty
make test           # pytest
make test-debug     # pytest, open debugger on first failure (ARGS=... to filter)
make test-coverage  # pytest with coverage report
make test-all       # all of the above
make build          # build sdist and wheel into dist/
```
