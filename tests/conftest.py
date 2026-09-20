from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    from hn_ingest.app import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client
