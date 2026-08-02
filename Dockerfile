# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: builder - installs Poetry and resolves/installs dependencies into
# an isolated virtualenv. Kept separate from the final stage so build-time
# tooling (Poetry itself, compilers for any wheel builds) never ends up in
# the production image.
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

ENV POETRY_VERSION=1.8.4 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PIP_NO_CACHE_DIR=1

# build-essential is required to build source distributions for packages
# without prebuilt wheels for the current platform/Python version.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:${PATH}"

WORKDIR /app

# Copy only dependency manifests first so this layer is cache-friendly -
# dependency installation is only re-run when these files actually change.
COPY pyproject.toml ./
# poetry.lock is intentionally not committed yet (see project notes) - if/when
# one is generated and committed, uncomment the line below for reproducible,
# pinned installs:
# COPY poetry.lock ./

# Install only production dependencies (no dev/test tooling) into ./.venv.
RUN poetry install --no-root --only main --no-ansi

# ---------------------------------------------------------------------------
# Stage 2: final runtime image - slim, no build toolchain, non-root user.
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

# Create an unprivileged user/group to run the app as - never run as root.
RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser

WORKDIR /app

# Bring in the pre-built virtualenv from the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Application source.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts
COPY entrypoint.sh ./

RUN chmod +x entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Runs pending Alembic migrations, then starts uvicorn. See entrypoint.sh.
ENTRYPOINT ["./entrypoint.sh"]
