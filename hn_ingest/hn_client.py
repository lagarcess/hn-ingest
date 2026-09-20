"""Hacker News Firebase client. Network I/O lives here only."""

from __future__ import annotations

from typing import Any

import httpx


class HNError(Exception):
    """Outbound HN API failure."""


class HNClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_new_ids(self, limit: int) -> list[int]:
        try:
            response = httpx.get(f"{self.base_url}/newstories.json", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise HNError(f"failed to fetch newstories: {exc}") from exc
        except ValueError as exc:
            raise HNError("newstories response was not JSON") from exc
        if not isinstance(data, list):
            raise HNError("newstories response was not a list")
        ids = [int(item_id) for item_id in data if isinstance(item_id, int)]
        return ids[:limit]

    def fetch_item(self, item_id: int) -> dict[str, Any] | None:
        try:
            response = httpx.get(
                f"{self.base_url}/item/{item_id}.json", timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise HNError(f"failed to fetch item {item_id}: {exc}") from exc
        except ValueError as exc:
            raise HNError(f"item {item_id} response was not JSON") from exc
        if data is None:
            return None
        if not isinstance(data, dict):
            raise HNError(f"item {item_id} response was not an object")
        return data
