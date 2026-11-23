<!-- docs/design/complejidad.md -->
# Accepted complexity

Every piece of complexity beyond the simplest version is logged here (plan section 2.1).

| Date | What was added | Problem it solves | Signal to remove it |
|---|---|---|---|
| 2026-11-10 | Tariffs in `app/tariffs.toml`, loaded and validated by `load_tariffs()` into a `TariffTable` (stage 1.1). | ARS prices change often: they are edited as data, not code, and a broken file fails at startup with the file and field in the message instead of producing wrong quotes. | Tariffs move to the database with validity dates (stage 2.1), or they stop changing. |
| 2026-11-10 | `ZONES` exposed as a read-only `MappingProxyType` (stage 1.1). | `frozen=True` protects each `ZoneTariff`, but a plain `dict` could still gain or lose zones at runtime. | Tariffs stop being a module-level shared object (for example, loaded per request from storage). |
