# Review notes

Implementation log for the hn-ingest service. `uploads/ARCHITECTURE.md` was not in the workspace; signatures below are the ones that landed on `main`.

## Module map and signatures

- `config.load_settings(environ=None) -> Settings` — only env-boundary reader (`DATABASE_PATH`, `PORT`, `LOG_LEVEL`, `HN_BASE_URL`)
- `process.classify_type(raw_type) -> str`
- `process.extract_domain(url) -> str | None`
- `process.normalize_time(unix_ts) -> str | None` (`…Z` UTC)
- `process.score_bucket(score) -> str` (`none` / `low` / `mid` / `high`)
- `process.process_item(item: dict) -> dict` — pure; no I/O
- `store.Store.upsert(item) -> int` — `INSERT … ON CONFLICT(id) DO UPDATE`
- `store.Store.get(id) -> dict | None`
- `store.Store.summary() -> dict`
- `HNClient.fetch_new_ids(limit) -> list[int]`
- `HNClient.fetch_item(id) -> dict | None`
- `create_app() -> FastAPI` — HTTP validation + orchestration only

Guards stay at HTTP/config boundaries. `process.py` does not import FastAPI, sqlite, or `os.environ`.

## Implementation facts

- **2026-09-20** `b6c2765` — empty `main` (`3fafebc`) blocked SDET. Landed health, `POST /ingest/items` (single object or `{items:[…]}`), `GET /items/{id}`, SQLite upsert, pytest happy/422/idempotent.
- **2026-09-20** `42b79cb` — derived fields wired through ingest. Type classification treats anything outside `{story,comment,job,poll}` as `unknown`. Score `0` is `low`; missing score is `none`. Domain lowercases host and strips `www.`.
- **2026-09-20** `dda8a52` — `/ingest/pull` talks to `HN_BASE_URL` (`/newstories.json`, `/item/{id}.json`). Null/invalid remote items are skipped; HN transport failure is `502`. `/summary` always returns the full type and bucket key sets. Pull tests hit a local HTTP fake HN (not patched internals).
- Persistence is one JSON document per row keyed by HN id. Enough for this size; summary scans all rows in-process.
- Duplicate `POST` of the same payload is 200 with the same stored row (deterministic `process_item` + upsert).
- **2026-09-20** — Dockerfile builds on `python:3.12-slim` and serves `GET /health` via uvicorn. `uploads/ARCHITECTURE.md` never appeared; README/REVIEW document the implemented map instead.

## Trunk-based tradeoff

Direct commits to `main` got a runnable, test-covered slice in front of SDET without PR latency. The cost is that a bad push is immediately everyone else's problem: there is no review gate, and revert is the rollback. That is acceptable here because each push was a small, already-green slice (pytest on the agent VM before `git push`), the blast radius is a greenfield service, and the alternative — feature branches plus PR ceremony — was explicitly rejected by the Tech Lead. Keep slices small enough that a revert is cheaper than a discussion; do not grow this habit to changes that need a second pair of eyes (auth, schema breakages, production data).
