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

Interactive documentation is available at `http://127.0.0.1:8000/docs`.

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
