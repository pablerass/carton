# 2. CLI and API parity

Date: 2026-11-09

## Status

Accepted

## Context

Carton started as a command line tool that exported a BoardGameGeek collection
to CSV, and is now also a FastAPI application. Both are useful: the API is how
the service is deployed and integrated, while the CLI is handy for one-off
queries, scripting and debugging BGG data without running a server.

If features are only added to one of them, the other one becomes stale and
eventually gets dropped, which is what happened briefly when the CSV export was
replaced by the API.

There were two ways of exposing both: a single `carton` command with a `serve`
subcommand that wraps `uvicorn.run`, or separate entrypoints. A `serve` wrapper
has to reimplement every server option (host, port, workers, proxy headers,
reload...) that uvicorn, or any other ASGI server, already provides.

## Decision

- The API and the CLI are separate entrypoints over the same code:
  - API: the ASGI app `carton.api:app`, run with an ASGI server such as
    `uvicorn carton.api:app`. Carton does not wrap the server.
  - CLI: the `carton` command (`carton.__main__:main`), with one subcommand per
    operation, e.g. `carton collection <user>`.
- **Every API endpoint must have an equivalent CLI subcommand**, added in the same
  change. For example `GET /users/{username}/collection` is
  `carton collection <username>`.
- The logic lives in the providers, models and shared modules (e.g.
  `carton.auth`). `carton/api.py` and `carton/__main__.py` stay thin: they only
  parse input, call that logic and format the output (JSON for the API; CSV or
  JSON for the CLI).
- The Docker image only runs the API.

## Consequences

- New features need both an endpoint and a subcommand, plus tests for both.
- Errors are mapped separately in each interface (HTTP status codes in the API,
  log messages and exit codes in the CLI).
- Logic duplicated between `api.py` and `__main__.py` is a sign it should move
  to a shared module.
- The CLI is used by running the package (`uv run carton`, `uv tool install`),
  not through the Docker image.
