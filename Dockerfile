FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first so this layer is reused when only the code changes
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-default-groups --no-install-project --no-editable

COPY README.md LICENSE.txt ./
COPY carton ./carton
RUN uv sync --locked --no-default-groups --no-editable


FROM python:3.14-slim

COPY --from=builder /app/.venv /app/.venv

# carton writes its export to ~/file.csv, so HOME points to the output directory
ENV PATH="/app/.venv/bin:$PATH" \
    HOME=/data

WORKDIR /data
USER 1000:1000

ENTRYPOINT ["carton"]
