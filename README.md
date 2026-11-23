<!-- README.md -->
# python-gcp-ai-lab

Portfolio lab: a fictional shipping quote service (prices in ARS) that will grow into an assistant answering questions about fictional shipping policies (RAG and a small agent) on Google Cloud.

## Stage status

Status values: **pending**, **local** (works on this machine), **blocked**, **verified in GCP**.

| Stage | What | Status | Record |
|---|---|---|---|
| 0.2 | Local environment, repo, pre-commit (gitleaks, ruff, mypy) | local | [docs/etapas/0.2.md](docs/etapas/0.2.md) |
| 1.1 | Pure quoting function with `Decimal`, tariffs in TOML | local | [docs/etapas/1.1.md](docs/etapas/1.1.md) |
| 1.2 | Async API with FastAPI (`/health`, `/quotes`) | local | [docs/etapas/1.2.md](docs/etapas/1.2.md) |
| 1.3 | Multi-stage Dockerfile with uv | blocked (image build, see record) | [docs/etapas/1.3.md](docs/etapas/1.3.md) |
| 2.1 | PostgreSQL + pgvector, SQLAlchemy async, Alembic, persistent quotes | local (database in compose, API on the host) | [docs/etapas/2.1.md](docs/etapas/2.1.md) |
| 1.4+ | Terraform, Cloud Run, Secret Manager, AI, operations | pending | |

Design notes: [docs/design/](docs/design/).

## Run locally

Requirements: [uv](https://docs.astral.sh/uv/) and Docker Desktop.

```
uv sync                          # create .venv from uv.lock (includes dev tools)
copy .env.example .env           # PowerShell; local configuration (never committed)
docker compose up --build        # PostgreSQL + API; the API migrates on startup
```

The API listens on <http://localhost:8000> (container port 8080); interactive docs at `/docs`.

```
curl.exe http://localhost:8000/health
curl.exe -X POST http://localhost:8000/quotes -H "Content-Type: application/json" -d "{\"zone\":\"amba\",\"weight_kg\":2.5,\"length_cm\":20,\"width_cm\":15,\"height_cm\":10,\"mode\":\"standard\"}"
curl.exe http://localhost:8000/quotes/<id>
```

In PowerShell use `curl.exe`: plain `curl` is an alias of `Invoke-WebRequest`.

To run the API on the host instead (database still in compose):

```
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Tests

| Command | Runs |
|---|---|
| `uv run pytest` | Unit tests only (quoting, tariffs): no database, no network. |
| `uv run pytest -m integration` | API integration tests against the compose database. |
| `uv run pytest -m ""` | Everything. |

Integration tests need the database up and migrated: `docker compose up -d db` and `uv run alembic upgrade head` (or a running `docker compose up`).

Lint and types: `uv run ruff check .` and `uv run mypy app`.
