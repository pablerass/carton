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

## Development

```sh
make lint           # ruff
make type-check     # ty
make test           # pytest
make test-coverage  # pytest with coverage report
make test-all       # all of the above
make build          # build sdist and wheel into dist/
```
