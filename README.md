# hn-ingest

Small FastAPI service that pulls or accepts Hacker News items, **derives** a few fields, upserts them into SQLite by HN `id`, and exposes read/summary endpoints.

`uploads/ARCHITECTURE.md` was not present in this workspace. The module map below is the one implemented.

## What was built

| Piece | Role |
| --- | --- |
| `hn_ingest/app.py` | FastAPI factory + HTTP guards |
| `hn_ingest/config.py` | `DATABASE_PATH`, `PORT`, `LOG_LEVEL`, `HN_BASE_URL` |
| `hn_ingest/models.py` | Pydantic v2 request/response models |
| `hn_ingest/process.py` | Pure derive: type, domain, `time_iso`, `score_bucket` |
| `hn_ingest/store.py` | SQLite upsert/get/summary (`sqlite3`) |
| `hn_ingest/hn_client.py` | Firebase `newstories` + `item/{id}` client |
| `tests/` | pytest + httpx `TestClient` against observable HTTP/JSON |

### API

- `GET /health` → `{"status":"ok"}`
- `POST /ingest/items` — one HN-shaped object **or** `{"items":[...]}`; 422 on bad input; upsert by HN id (idempotent 200)
- `POST /ingest/pull?limit=20` — fetch `newstories` + items from `HN_BASE_URL`, process, upsert; `{count, ids}`
- `GET /items/{id}` — processed record or 404
- `GET /summary` — totals by type, top domains, score buckets

### Processing

For each item (not a raw dump):

- **type**: `story` / `comment` / `job` / `poll` / `unknown`
- **domain**: host from `url` (`www.` stripped)
- **time_iso**: Unix `time` → UTC `YYYY-MM-DDTHH:MM:SSZ`
- **score_bucket**: `none` if score missing; `low` &lt; 50; `mid` &lt; 200; `high` otherwise

## What was skipped (out of scope)

Queue, GraphQL, Kubernetes, auth, ML, managed Postgres, frontend, DigitalOcean resources.

## Run locally

Python 3.12+. From the repo root:

```bash
python3 -m pip install -r requirements.txt
export DATABASE_PATH=data/hn.db
python3 -m uvicorn hn_ingest.app:app --host 0.0.0.0 --port 8000
```

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/ingest/items \
  -H 'content-type: application/json' \
  -d '{"id":8863,"type":"story","title":"Dropbox","url":"http://www.getdropbox.com/u/2/screencast.html","score":111,"time":1175714200}'
curl -s localhost:8000/items/8863
curl -s -X POST 'localhost:8000/ingest/pull?limit=5'
curl -s localhost:8000/summary
```

### Tests

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

### Docker

```bash
docker build -t hn-ingest .
docker run --rm -p 8000:8000 hn-ingest
```

## 10× notes

This slice is sized for a single process and a local SQLite file.

- **10× ingest volume**: sequential `httpx` pulls will stall on HN latency. Fan-out with a small worker pool or async client, cap concurrency, and persist a high-water HN id so `/ingest/pull` is incremental.
- **10× readers**: move `summary` off a full-table JSON scan onto indexed columns (or a rollup table updated on upsert). SQLite still works if one writer; many writers want Postgres and a real connection pool.
- **10× operators**: add structured request logs, a `/ready` that checks DB + HN, and deploy as a stateless container with the DB on a volume — not a queue/K8s rewrite.

## Config

| Env | Default |
| --- | --- |
| `DATABASE_PATH` | `data/hn.db` |
| `PORT` | `8000` |
| `LOG_LEVEL` | `info` |
| `HN_BASE_URL` | `https://hacker-news.firebaseio.com/v0` |
