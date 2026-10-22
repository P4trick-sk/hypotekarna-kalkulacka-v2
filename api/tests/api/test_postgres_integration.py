"""Integračný test proti skutočnej databáze. Spustí sa len s DATABASE_URL (z api/.env):

uv run pytest -m integration
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app

from .conftest import DEFAULT_BODY

real = Settings()
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not real.db_configured, reason="DATABASE_URL nie je nastavená"),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = real.model_copy(update={"calc_log_enabled": False, "rate_limit": "10000/minute"})
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        yield c


def test_scenario_lifecycle_against_supabase(client: TestClient) -> None:
    owner = {"X-Client-Id": str(uuid4())}
    stranger = {"X-Client-Id": str(uuid4())}
    assert client.get("/api/v1/health").json()["db"] == "ok"

    created = client.post(
        "/api/v1/scenarios",
        json={"name": "Integračný test", "inputs": DEFAULT_BODY},
        headers=owner,
    )
    assert created.status_code == 201, created.text
    sid = created.json()["id"]
    try:
        assert created.json()["monthly_total"] == "1366.04"
        assert [s["id"] for s in client.get("/api/v1/scenarios", headers=owner).json()] == [sid]
        assert client.get("/api/v1/scenarios", headers=stranger).json() == []
        assert client.get(f"/api/v1/scenarios/{sid}", headers=stranger).status_code == 404

        patched = client.patch(
            f"/api/v1/scenarios/{sid}",
            json={"name": "Premenovaný", "inputs": {**DEFAULT_BODY, "currency": "CZK"}},
            headers=owner,
        ).json()
        assert (patched["name"], patched["currency"]) == ("Premenovaný", "CZK")
        assert patched["updated_at"] > created.json()["updated_at"]

        slug = client.post(f"/api/v1/scenarios/{sid}/share", headers=owner).json()["slug"]
        shared = client.get(f"/api/v1/share/{slug}")
        assert shared.status_code == 200
        assert sid not in shared.text and owner["X-Client-Id"] not in shared.text

        assert client.delete(f"/api/v1/scenarios/{sid}/share", headers=owner).status_code == 204
        assert client.get(f"/api/v1/share/{slug}").status_code == 404
    finally:
        assert client.delete(f"/api/v1/scenarios/{sid}", headers=owner).status_code == 204
    assert client.get(f"/api/v1/scenarios/{sid}", headers=owner).status_code == 404
