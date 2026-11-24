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
| 2026-11-24 | Remote Terraform state in a GCS bucket created by a separate `infra/bootstrap/` root (stage 1.4). | The state of resources that bill while idle must survive the local machine, be versioned, and be locked against concurrent runs. | The lab is retired (B6): the bucket is the last thing destroyed. |
| 2026-11-24 | `random_id` suffix on the Cloud SQL instance name, overridable with `var.sql_suffix` (stage 3.7). | A deleted Cloud SQL name cannot be reused for a while, so a later `apply` after `destroy` would fail with a fixed name. | Never, while instances are created and destroyed in windows. |
| 2026-11-24 | `Settings` builds the database URL from `DB_*` parts and `INSTANCE_CONNECTION_NAME` when `DATABASE_URL` is absent (stage 1.5). | On Cloud Run the password comes alone from Secret Manager; a full URL secret would duplicate the user, database and instance already known to Terraform. | The password is replaced by IAM database authentication (no password at all). |
