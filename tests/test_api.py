from __future__ import annotations

SAMPLE_STORY = {
    "id": 8863,
    "type": "story",
    "by": "dhouston",
    "time": 1175714200,
    "title": "My YC app: Dropbox - Throw away your USB drive",
    "url": "http://www.getdropbox.com/u/2/screencast.html",
    "score": 111,
}


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_single_item_and_get(client):
    response = client.post("/ingest/items", json=SAMPLE_STORY)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["ids"] == [8863]

    fetched = client.get("/items/8863")
    assert fetched.status_code == 200
    record = fetched.json()
    assert record["id"] == 8863
    assert record["title"] == SAMPLE_STORY["title"]
    assert record["url"] == SAMPLE_STORY["url"]
    assert record["score"] == 111


def test_ingest_items_wrapper(client):
    response = client.post(
        "/ingest/items",
        json={"items": [{"id": 1, "type": "comment"}, {"id": 2, "type": "job"}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["ids"] == [1, 2]
    assert client.get("/items/1").json()["type"] == "comment"
    assert client.get("/items/2").json()["type"] == "job"


def test_ingest_bad_payload_422(client):
    missing_id = client.post("/ingest/items", json={"title": "no identifier"})
    assert missing_id.status_code == 422

    bad_id_type = client.post("/ingest/items", json={"id": "not-an-int"})
    assert bad_id_type.status_code == 422

    wrapper_missing_id = client.post(
        "/ingest/items", json={"items": [{"title": "still no id"}]}
    )
    assert wrapper_missing_id.status_code == 422

    bare_list = client.post("/ingest/items", json=[{"id": 1}])
    assert bare_list.status_code == 422


def test_duplicate_ingest_is_idempotent(client):
    first = client.post("/ingest/items", json=SAMPLE_STORY)
    second = client.post("/ingest/items", json=SAMPLE_STORY)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()

    stored = client.get("/items/8863")
    assert stored.status_code == 200
    again = client.get("/items/8863")
    assert again.status_code == 200
    assert stored.json() == again.json()
    assert stored.json()["id"] == 8863


def test_get_missing_item_404(client):
    response = client.get("/items/999999")
    assert response.status_code == 404
