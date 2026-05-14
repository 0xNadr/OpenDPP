# Multi-stage Dockerfile for the OpenDPP API.
# Build targets:
#   --target dev   → uvicorn with --reload, source mounted at runtime
#   --target prod  → frozen image with installed source

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH=/app/.venv/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /usr/local/bin/

WORKDIR /app


# --- deps stage: install dependencies into a cached layer ---------------------
FROM base AS deps

COPY api/pyproject.toml api/uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


# --- dev stage: includes dev deps, expects source via bind mount --------------
FROM base AS dev

COPY api/pyproject.toml api/uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Source is mounted in via docker compose at /app/src; schemas at /schemas.
# Project isn't installed (so the bind mount stays authoritative); PYTHONPATH
# lets the interpreter find the `opendpp` package directly.
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["uvicorn", "opendpp.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/src", "--reload-dir", "/schemas"]


# --- prod stage: copy source, install package, no dev deps --------------------
FROM deps AS prod

COPY api/ /app/
COPY schemas/ /schemas/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uvicorn", "opendpp.main:app", "--host", "0.0.0.0", "--port", "8000"]
