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

The project exposes a `carton` command:

```sh
uv run carton --bgg-user <user> --bgg-api-key <api-key>
# or
uv run carton --bgg-user <user> --bgg-password <password>
```

Credentials can also be provided via the `BGG_USER`, `BGG_PASSWORD` and
`BGG_API_KEY` environment variables. Run `uv run carton --help` for all
options.

To install the command globally as a tool:

```sh
uv tool install .
carton --help
```

## Docker

Copy the example environment file and fill in your BoardGameGeek credentials:

```sh
cp .env.example .env
```

Then build the image and run the command:

```sh
docker compose build
docker compose run --rm carton
```

Arguments are passed to `carton`, for example
`docker compose run --rm carton --help`. The collection is printed and exported
to `output/file.csv`. The container runs as UID/GID 1000; if your host user is
different, set `CARTON_UID` and `CARTON_GID` so it can write to `output/`.

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
