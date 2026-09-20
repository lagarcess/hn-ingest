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
