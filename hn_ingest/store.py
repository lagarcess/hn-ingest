"""SQLite persistence. Upsert is keyed on HN item id."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any


class Store:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        parent = os.path.dirname(os.path.abspath(database_path))
        if parent:
            os.makedirs(parent, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    data TEXT NOT NULL
                )
                """
            )

    def upsert(self, item: dict[str, Any]) -> int:
        item_id = int(item["id"])
        payload = json.dumps(item, sort_keys=True, separators=(",", ":"))
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO items (id, data) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET data = excluded.data
                """,
                (item_id, payload),
            )
        return item_id

    def get(self, item_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT data FROM items WHERE id = ?", (item_id,)
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["data"])

    def all_items(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT data FROM items ORDER BY id").fetchall()
        return [json.loads(row["data"]) for row in rows]

    def summary(self) -> dict[str, Any]:
        items = self.all_items()
        by_type = {"story": 0, "comment": 0, "job": 0, "poll": 0, "unknown": 0}
        score_buckets = {"none": 0, "low": 0, "mid": 0, "high": 0}
        domains: dict[str, int] = {}
        for item in items:
            item_type = item.get("type")
            if item_type not in by_type:
                item_type = "unknown"
            by_type[item_type] += 1
            bucket = item.get("score_bucket")
            if bucket not in score_buckets:
                bucket = "none"
            score_buckets[bucket] += 1
            domain = item.get("domain")
            if isinstance(domain, str) and domain:
                domains[domain] = domains.get(domain, 0) + 1
        top_domains = [
            {"domain": domain, "count": count}
            for domain, count in sorted(domains.items(), key=lambda pair: (-pair[1], pair[0]))[:10]
        ]
        return {
            "total": len(items),
            "by_type": by_type,
            "top_domains": top_domains,
            "score_buckets": score_buckets,
        }
