from __future__ import annotations

from fastapi.testclient import TestClient

from tests.fake_hn import FakeHNServer


def _client(tmp_path, monkeypatch, hn_base_url: str) -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("HN_BASE_URL", hn_base_url)
    from hn_ingest.app import create_app

    return TestClient(create_app())


def test_pull_fetches_processes_and_upserts(tmp_path, monkeypatch):
    hn = FakeHNServer(
        newstory_ids=[101, 102, 103],
        items={
            101: {
                "id": 101,
                "type": "story",
                "title": "One",
                "url": "https://www.example.com/a",
                "score": 12,
                "time": 1175714200,
            },
            102: None,
            103: {
                "id": 103,
                "type": "job",
                "title": "Hiring",
                "url": "https://jobs.example.org/x",
                "score": 80,
                "time": 1175714200,
            },
        },
    )
    base = hn.start()
    try:
        with _client(tmp_path, monkeypatch, base) as client:
            first = client.post("/ingest/pull", params={"limit": 3})
            assert first.status_code == 200
            body = first.json()
            assert body["count"] == 2
            assert body["ids"] == [101, 103]

            story = client.get("/items/101").json()
            assert story["type"] == "story"
            assert story["domain"] == "example.com"
            assert story["score_bucket"] == "low"
            assert story["time_iso"] == "2007-04-04T19:16:40Z"

            job = client.get("/items/103").json()
            assert job["type"] == "job"
            assert job["domain"] == "jobs.example.org"
            assert job["score_bucket"] == "mid"

            second = client.post("/ingest/pull", params={"limit": 3})
            assert second.status_code == 200
            assert second.json() == first.json()
            assert client.get("/items/101").json() == story
    finally:
        hn.stop()


def test_pull_bad_limit_422(tmp_path, monkeypatch):
    hn = FakeHNServer(newstory_ids=[], items={})
    base = hn.start()
    try:
        with _client(tmp_path, monkeypatch, base) as client:
            assert client.post("/ingest/pull", params={"limit": 0}).status_code == 422
            assert client.post("/ingest/pull", params={"limit": -1}).status_code == 422
    finally:
        hn.stop()


def test_pull_hn_down_502(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, "http://127.0.0.1:1") as client:
        response = client.post("/ingest/pull")
        assert response.status_code == 502


def test_summary_empty_and_populated(client):
    empty = client.get("/summary")
    assert empty.status_code == 200
    assert empty.json() == {
        "total": 0,
        "by_type": {"story": 0, "comment": 0, "job": 0, "poll": 0, "unknown": 0},
        "top_domains": [],
        "score_buckets": {"none": 0, "low": 0, "mid": 0, "high": 0},
    }

    payload = {
        "items": [
            {
                "id": 1,
                "type": "story",
                "url": "https://www.example.com/a",
                "score": 10,
            },
            {
                "id": 2,
                "type": "story",
                "url": "https://example.com/b",
                "score": 80,
            },
            {
                "id": 3,
                "type": "comment",
                "score": 250,
            },
            {"id": 4, "type": "pollopt"},
        ]
    }
    assert client.post("/ingest/items", json=payload).status_code == 200
    summary = client.get("/summary").json()
    assert summary["total"] == 4
    assert summary["by_type"] == {
        "story": 2,
        "comment": 1,
        "job": 0,
        "poll": 0,
        "unknown": 1,
    }
    assert summary["score_buckets"] == {"none": 1, "low": 1, "mid": 1, "high": 1}
    assert summary["top_domains"] == [{"domain": "example.com", "count": 2}]
