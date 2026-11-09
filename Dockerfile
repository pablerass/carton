FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# cartucho is a local path dependency (../cartucho), provided as the 'cartucho' build context
COPY --from=cartucho pyproject.toml README.md LICENSE.txt /cartucho/
COPY --from=cartucho cartucho /cartucho/cartucho

# Install dependencies first so this layer is reused when only the code changes
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-default-groups --no-install-project --no-editable

COPY README.md LICENSE.txt ./
COPY carton ./carton
RUN uv sync --locked --no-default-groups --no-editable


FROM python:3.14-slim

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    CARTON_CACHE_FILE=/data/bgg.pickle

# Cached BGG games, mount a volume here to keep them between containers
RUN mkdir /data && chown 1000:1000 /data
VOLUME /data

USER 1000:1000
EXPOSE 8000

CMD ["uvicorn", "carton.api:app", "--host", "0.0.0.0", "--port", "8000"]
