<!-- docs/design/complejidad.md -->
# Accepted complexity

Every piece of complexity beyond the simplest version is logged here (plan section 2.1).

| Date | What was added | Problem it solves | Signal to remove it |
|---|---|---|---|
| 2026-11-10 | Tariffs in `app/tariffs.toml`, loaded and validated by `load_tariffs()` into a `TariffTable` (stage 1.1). | ARS prices change often: they are edited as data, not code, and a broken file fails at startup with the file and field in the message instead of producing wrong quotes. | Tariffs move to the database with validity dates (stage 2.1), or they stop changing. |
| 2026-11-10 | `ZONES` exposed as a read-only `MappingProxyType` (stage 1.1). | `frozen=True` protects each `ZoneTariff`, but a plain `dict` could still gain or lose zones at runtime. | Tariffs stop being a module-level shared object (for example, loaded per request from storage). |
| 2026-11-23 | Settings and the database engine are created lazily and cached (`lru_cache` in `get_settings()` and `get_engine()`), not at import time (stage 2.1). | Unit tests and tools that import `app` work without `DATABASE_URL` or a database. | Every process that imports `app` always has a database (then a module-level engine is simpler). |
| 2026-11-23 | `pool_pre_ping=True` on the engine (stage 2.1). | After a database restart the first request returned 500 because the pool held a dead connection. Verified: with pre-ping the first request after `docker compose restart db` returns 200. | Never; the cost is one tiny round trip per checkout. Revisit only if latency measurements show it matters. |
| 2026-11-23 | Integration tests marked `integration` and excluded by default (`addopts = "-m 'not integration'"`) (stage 2.1). | `uv run pytest` stays fast and works without Docker; integration runs explicitly with `-m integration`. | CI always provides a database and runs everything (stage 4.2). |
