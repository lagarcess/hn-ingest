"""Pure item processing. No I/O, no HTTP, no environment access."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

KNOWN_TYPES = frozenset({"story", "comment", "job", "poll"})


def classify_type(raw_type: Any) -> str:
    if isinstance(raw_type, str) and raw_type in KNOWN_TYPES:
        return raw_type
    return "unknown"


def extract_domain(url: Any) -> str | None:
    if not isinstance(url, str) or not url.strip():
        return None
    raw = url.strip()
    parsed = urlparse(raw if "://" in raw else f"//{raw}")
    host = parsed.netloc or parsed.path.split("/")[0]
    host = host.split("@")[-1]
    host = host.split(":")[0]
    host = host.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host or None


def normalize_time(unix_ts: Any) -> str | None:
    if unix_ts is None:
        return None
    if isinstance(unix_ts, bool) or not isinstance(unix_ts, (int, float)):
        return None
    try:
        dt = datetime.fromtimestamp(int(unix_ts), tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def score_bucket(score: Any) -> str:
    if score is None:
        return "none"
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return "none"
    if score < 50:
        return "low"
    if score < 200:
        return "mid"
    return "high"


def process_item(item: dict[str, Any]) -> dict[str, Any]:
    """Derive classified type, domain, ISO time, and score bucket."""
    processed = dict(item)
    processed["type"] = classify_type(item.get("type"))
    processed["domain"] = extract_domain(item.get("url"))
    processed["time_iso"] = normalize_time(item.get("time"))
    processed["score_bucket"] = score_bucket(item.get("score"))
    return processed
