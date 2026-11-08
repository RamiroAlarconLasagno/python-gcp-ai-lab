<!-- CLAUDE.md -->
# python-gcp-ai-lab

Portfolio lab for a Senior Backend Python role (Google Cloud, Gemini). One product: a fictional shipping quote service plus an assistant that answers questions about fictional shipping policies (RAG and a small agent). Full plan: `docs/PLAN.md` (read only the stage you are working on). Progress: `docs/AVANCE.md`.

## How to work with me
- Respond in Spanish. Repo docs (README, design notes, TDD) in English. Commits in Spanish, imperative, with the stage id: `1.1: agrega cotizador puro con pruebas`.
- One stage at a time. Before implementing, propose a short plan and wait for my approval. Work in small steps and run what you write.
- Explain every command you propose: what it does and why. I am learning; do not skip this.
- Before a technical choice, offer alternatives with a recommendation and let me decide.
- Verify library, SDK, model and price versions in current docs or with `uv add`, never from memory.
- First line of every file: a comment with its relative path. Fix the original file; never create copies.
- Commit messages: Spanish subject line with the stage id (max ~72 chars), a blank line, then a body with bullets explaining what changed and why, plus what was verified.

## Simplicity rule (plan section 2.1)
- Start with the simplest version that meets the requirement: function, then module, then class, then interface or pattern.
- No `Protocol`/`ABC` until two real implementations exist. No Repository, Unit of Work or DI containers.
- A new abstraction needs a second real use, a concrete problem or a requirement. "Might need it later" does not count.
- Accepted complexity is logged in `docs/design/complejidad.md`.

## Never without my explicit confirmation in the chat
- Destructive commands (`terraform destroy`, `gcloud ... delete`, deleting files outside the repo).
- Creating resources that bill while idle (Cloud SQL, GKE, Vertex endpoints, reserved IPs).
- Creating service account keys. Never commit secrets, `.env`, `*.tfstate*` or `*.tfvars`.

## Stack and commands
- Windows native, PowerShell. Python 3.13 managed by `uv`.
- Dependencies: `uv add <pkg>` (dev tools: `uv add --dev <pkg>`). Never `pip install`.
- Environment: `uv sync` creates or updates `.venv` from `uv.lock`, including the `dev` group (pytest, ruff, mypy).
- Tests: `uv run pytest`. Single test: `uv run pytest tests/test_smoke.py::test_app_is_importable`.
- Lint: `uv run ruff check .`. Types: `uv run mypy app` (only `app/`; tests are not type-checked).
- Layout: `app/` (flat modules: `main.py`, `quoting.py`, `db.py`, `llm.py`...), `tests/`, `infra/` (Terraform), `scripts/`, `docs/`.
- Identifiers in English (no accents or ñ). Docstrings in Spanish.

## Google Cloud
- Project: `python-gcp-ai-lab`. Gemini models on the `global` endpoint. Infrastructure region: pending decision.
- Auth: ADC locally, runtime service account on Cloud Run, Workload Identity Federation in CI. No JSON keys.
- Label every resource `lab=gcp-ai`.

## Closing a stage
Check the stage's "done when", ask me the 3 questions (why this option, how it fails, what it costs and how it is deleted), remind me to run `scripts/inventario.sh` (a bash script: from Git Bash, `bash scripts/inventario.sh`), and update `docs/AVANCE.md` and `docs/etapas/<id>.md`.
