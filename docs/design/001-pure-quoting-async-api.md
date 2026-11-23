<!-- docs/design/001-pure-quoting-async-api.md -->
# ND-001: Pure quoting function behind an async FastAPI API

- **Status:** proposed
- **Date:** 2026-11-23
- **Authoring:** AI-assisted draft, to be reviewed and rewritten by Ramiro.

## Context

The product needs shipping quotes (price and delivery time) over HTTP. The same calculation will later be used by other callers: the persistence layer (stage 2.1) and the assistant agent's `get_quote` tool (stage 3.6), which must never invent a price. Money must be exact, and the rules (volumetric weight, rounding up to the next kilo, 30 kg limit, urgent surcharge) must be easy to test and explain.

## Decision

1. **Pure function with `Decimal`.** `calculate_quote()` in `app/quoting.py` takes plain values and returns a frozen `Quote` dataclass. It does no I/O, has no framework imports and uses `Decimal` with `ROUND_HALF_UP` for money. Tariffs come from a validated TOML file (`app/tariffs.toml`).
2. **Thin async API with FastAPI.** `app/main.py` exposes `GET /health` and `POST /quotes` as `async def` endpoints. Pydantic v2 models validate the shape of the request (required fields, numbers > 0) and serialize `Decimal` values as strings. Business-rule errors raised by the function (`ValueError`) are returned as 422 with the same `detail` format that Pydantic uses: `[{"loc", "msg", "type"}]`, where `type` is `business_rule`.
3. **No extra layers.** No routers, service classes or dependency injection until a second real use requires them (plan section 2.1).

## Alternatives considered

| Alternative | Why not |
|---|---|
| Business logic inside the endpoint | Harder to test without HTTP, and it cannot be reused by the database layer or the agent tool. |
| Flask | Synchronous by default, with no built-in request validation or OpenAPI docs. The upcoming async I/O (PostgreSQL with asyncpg, Gemini calls) fits an async framework better. |
| Django / Django REST Framework | Brings an ORM, admin and project structure that this small service does not need. It would add complexity without a concrete problem to solve. |

## Risks

- **Blocking the event loop.** The calculation runs inside `async def` endpoints. That is fine while it takes microseconds. A heavy, CPU-bound calculation would block every other request on the worker. Mitigation if that ever happens: run it in a thread pool (`run_in_threadpool`) or switch that endpoint to a plain `def`.
- **Two validation layers.** Shape is validated in Pydantic and business rules in the function. A rule that exists in only one of them can drift; the API tests cover both kinds of 422.

## Cost

None. No cloud resources; it runs locally and in tests.

## Verification

- Unit tests for the pure function and the tariff loader (`tests/test_quoting.py`, `tests/test_tariffs.py`), with no network or database.
- API tests with `httpx.AsyncClient` and `ASGITransport` (`tests/test_api.py`): health, a valid quote, and 422 for an incomplete body, a negative number, an unknown zone or mode and the "balloon" parcel.
- Manual check with `uv run uvicorn app.main:app --reload`: `/health`, `/quotes` and `/docs` respond.
