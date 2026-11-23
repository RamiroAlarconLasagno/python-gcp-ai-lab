# Dockerfile
# Multi-stage build: uv installs the locked dependencies in a builder stage and the
# final image keeps only the virtual environment and the code (no uv, no dev tools).

# Builder: same base image as the final stage, so the venv's Python path matches.
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

# Compile bytecode for faster startup; copy instead of hardlink (cache is a mount);
# use the image's Python instead of downloading one.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first (cached layer while uv.lock and pyproject.toml do not change).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


# Final image: Python only, non-root user.
FROM python:3.13-slim

RUN groupadd --system --gid 999 app \
 && useradd --system --gid 999 --uid 999 --create-home app

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8080

USER app
WORKDIR /app
EXPOSE 8080

# Shell form so ${PORT} is expanded (Cloud Run sets PORT); exec makes uvicorn PID 1.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
