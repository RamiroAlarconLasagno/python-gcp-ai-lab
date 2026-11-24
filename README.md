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
| 1.3 | Multi-stage Dockerfile with uv | local | [docs/etapas/1.3.md](docs/etapas/1.3.md) |
| 2.1 | PostgreSQL + pgvector, SQLAlchemy async, Alembic, persistent quotes | local | [docs/etapas/2.1.md](docs/etapas/2.1.md) |
| 1.4 | Terraform with remote state (GCS), inventory script | verified in GCP | [docs/etapas/1.4.md](docs/etapas/1.4.md) |
| 1.5 | Private Cloud Run service, Artifact Registry, runtime service account | verified in GCP | [docs/etapas/1.5.md](docs/etapas/1.5.md) |
| 3.7 | Cloud SQL window (PostgreSQL 17 + pgvector), migration job | verified in GCP (retire in B6) | [docs/etapas/3.7.md](docs/etapas/3.7.md) |
| 3.1+ | AI (RAG, agent), operations, CI/CD | pending | |

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

## Deploy to Google Cloud

The cloud environment is temporary: it bills while it exists (mainly Cloud SQL, about US$0.55/day). Costs and the ordered retirement steps are in [docs/costos-y-retiro.md](docs/costos-y-retiro.md).

Requirements: Terraform, the gcloud CLI, and Application Default Credentials (`gcloud auth application-default login`). No service account keys are used. Region: `us-central1`. Every resource is labeled `lab=gcp-ai`.

```
# 1. Remote state bucket (once; its own state stays local)
terraform -chdir=infra/bootstrap init
terraform -chdir=infra/bootstrap apply

# 2. APIs, Artifact Registry and the runtime service account (the registry must exist before the push)
terraform -chdir=infra init
terraform -chdir=infra apply -var "image=unused" -target=google_project_service.enabled -target=google_artifact_registry_repository.docker -target=google_service_account.runtime

# 3. Build and push the image
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build -t us-central1-docker.pkg.dev/python-gcp-ai-lab/quotes/api:<tag> .
docker push us-central1-docker.pkg.dev/python-gcp-ai-lab/quotes/api:<tag>

# 4. Everything else (Cloud SQL, secret, Cloud Run service and migration job)
terraform -chdir=infra apply -var "image=us-central1-docker.pkg.dev/python-gcp-ai-lab/quotes/api:<tag>"
gcloud run jobs execute quotes-migrate --region us-central1 --wait
```

The service is private: call it with an identity token.

```
curl.exe -H "Authorization: Bearer $(gcloud auth print-identity-token)" <service_url>/health
```

`<service_url>` comes from `terraform -chdir=infra output service_url`. To see what exists in the project, run `bash scripts/inventario.sh` from Git Bash.

### Retire

```
terraform -chdir=infra destroy -var "image=unused"
terraform -chdir=infra/bootstrap destroy
bash scripts/inventario.sh   # nothing from the lab should remain
```

## Tests

| Command | Runs |
|---|---|
| `uv run pytest` | Unit tests only (quoting, tariffs): no database, no network. |
| `uv run pytest -m integration` | API integration tests against the compose database. |
| `uv run pytest -m ""` | Everything. |

Integration tests need the database up and migrated: `docker compose up -d db` and `uv run alembic upgrade head` (or a running `docker compose up`).

Lint and types: `uv run ruff check .` and `uv run mypy app`.
