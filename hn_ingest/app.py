"""FastAPI application factory and HTTP routes."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from hn_ingest.config import load_settings
from hn_ingest.models import HealthResponse, HNItemIn, IngestRequest, IngestResponse
from hn_ingest.process import process_item
from hn_ingest.store import Store


def create_app() -> FastAPI:
    settings = load_settings()
    store = Store(settings.database_path)
    store.init()

    app = FastAPI(title="hn-ingest", version="0.1.0")
    app.state.settings = settings
    app.state.store = store

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post("/ingest/items", response_model=IngestResponse)
    def ingest_items(body: IngestRequest) -> IngestResponse:
        store_: Store = app.state.store
        ids: list[int] = []
        for raw in body.items:
            record = _to_stored_record(raw)
            ids.append(store_.upsert(record))
        return IngestResponse(count=len(ids), ids=ids)

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict[str, Any]:
        store_: Store = app.state.store
        record = store_.get(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="item not found")
        return record

    return app


def _to_stored_record(item: HNItemIn) -> dict[str, Any]:
    return process_item(item.model_dump())


app = create_app()
