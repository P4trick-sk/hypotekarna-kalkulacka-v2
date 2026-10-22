from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db.repos import ScenarioRow
from app.deps import get_log_repo, get_scenario_repo
from app.main import create_app

from .conftest import DEFAULT_BODY, FakeLogRepo

OWNER = "11111111-1111-4111-8111-111111111111"
STRANGER = "22222222-2222-4222-8222-222222222222"


class FakeScenarioRepo:
    def __init__(self) -> None:
        self.rows: dict[UUID, ScenarioRow] = {}

    def ping(self) -> None:
        return None

    def list(self, client_id: UUID) -> list[ScenarioRow]:
        rows = [r for r in self.rows.values() if r.client_id == client_id]
        return sorted(rows, key=lambda r: r.updated_at, reverse=True)

    def count(self, client_id: UUID) -> int:
        return len(self.list(client_id))

    def create(
        self, client_id: UUID, name: str, inputs: dict[str, Any], currency: str
    ) -> ScenarioRow:
        now = datetime.now(UTC)
        row = ScenarioRow(uuid4(), client_id, name, inputs, currency, None, now, now)
        self.rows[row.id] = row
        return row

    def get(self, client_id: UUID, scenario_id: UUID) -> ScenarioRow | None:
        row = self.rows.get(scenario_id)
        return row if row and row.client_id == client_id else None

    def update(
        self, client_id: UUID, scenario_id: UUID, changes: dict[str, Any]
    ) -> ScenarioRow | None:
        row = self.get(client_id, scenario_id)
        if row is None:
            return None
        row = replace(row, **changes, updated_at=datetime.now(UTC))
        self.rows[row.id] = row
        return row

    def delete(self, client_id: UUID, scenario_id: UUID) -> bool:
        if self.get(client_id, scenario_id) is None:
            return False
        del self.rows[scenario_id]
        return True

    def get_by_slug(self, slug: str) -> ScenarioRow | None:
        return next((r for r in self.rows.values() if r.share_slug == slug), None)


@pytest.fixture
def repo() -> FakeScenarioRepo:
    return FakeScenarioRepo()


@pytest.fixture
def client(
    settings: Settings, log_repo: FakeLogRepo, repo: FakeScenarioRepo
) -> Iterator[TestClient]:
    settings = settings.model_copy(update={"public_app_url": "http://localhost:5173"})
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_log_repo] = lambda: log_repo
    app.dependency_overrides[get_scenario_repo] = lambda: repo
    with TestClient(app) as c:
        yield c


def headers(client_id: str = OWNER) -> dict[str, str]:
    return {"X-Client-Id": client_id}


def create(client: TestClient, name: str = "Byt Košice", **inputs: Any) -> dict[str, Any]:
    response = client.post(
        "/api/v1/scenarios",
        json={"name": name, "inputs": {**DEFAULT_BODY, **inputs}},
        headers=headers(),
    )
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def test_A09_missing_client_id(client: TestClient) -> None:
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 400
    assert response.json()["errors"][0]["code"] == "missing_client_id"


def test_A10_invalid_client_id(client: TestClient) -> None:
    response = client.get("/api/v1/scenarios", headers=headers("abc"))
    assert response.status_code == 400
    assert response.json()["errors"][0]["code"] == "invalid_client_id"


def test_A11_create_and_list(client: TestClient) -> None:
    created = create(client)
    assert created["monthly_total"] == "1366.04"
    assert created["inputs"]["currency"] == "EUR"
    listed = client.get("/api/v1/scenarios", headers=headers()).json()
    assert [s["name"] for s in listed] == ["Byt Košice"]


def test_A11_name_is_trimmed_and_limited(client: TestClient) -> None:
    assert create(client, name="  Dom  ")["name"] == "Dom"
    response = client.post(
        "/api/v1/scenarios",
        json={"name": "x" * 101, "inputs": DEFAULT_BODY},
        headers=headers(),
    )
    assert response.status_code == 422


def test_A12_foreign_scenario_is_not_found(client: TestClient) -> None:
    sid = create(client)["id"]
    assert client.get(f"/api/v1/scenarios/{sid}", headers=headers(STRANGER)).status_code == 404
    assert client.get(f"/api/v1/scenarios/{sid}", headers=headers()).status_code == 200


def test_A13_foreign_delete_is_not_found(client: TestClient, repo: FakeScenarioRepo) -> None:
    sid = create(client)["id"]
    assert client.delete(f"/api/v1/scenarios/{sid}", headers=headers(STRANGER)).status_code == 404
    assert len(repo.rows) == 1
    assert client.delete(f"/api/v1/scenarios/{sid}", headers=headers()).status_code == 204
    assert repo.rows == {}


def test_A14_limit_of_50_scenarios(client: TestClient, repo: FakeScenarioRepo) -> None:
    for i in range(50):
        repo.create(UUID(OWNER), f"s{i}", {}, "EUR")
    response = client.post(
        "/api/v1/scenarios", json={"name": "51.", "inputs": DEFAULT_BODY}, headers=headers()
    )
    assert response.status_code == 409


def test_A15_invalid_inputs_are_not_saved(client: TestClient, repo: FakeScenarioRepo) -> None:
    response = client.post(
        "/api/v1/scenarios",
        json={"name": "zlý", "inputs": {**DEFAULT_BODY, "down_payment": "400000"}},
        headers=headers(),
    )
    assert response.status_code == 422
    assert repo.rows == {}


def test_patch_rename_and_overwrite(client: TestClient) -> None:
    sid = create(client)["id"]
    response = client.patch(
        f"/api/v1/scenarios/{sid}",
        json={
            "name": "Nový",
            "inputs": {**DEFAULT_BODY, "currency": "CZK", "extra_monthly": "100"},
        },
        headers=headers(),
    )
    data = response.json()
    assert (data["name"], data["currency"], data["monthly_total"]) == ("Nový", "CZK", "1466.04")


def test_A16_share_slug(client: TestClient) -> None:
    sid = create(client)["id"]
    data = client.post(f"/api/v1/scenarios/{sid}/share", headers=headers()).json()
    assert re.fullmatch(r"[A-Za-z0-9]{10}", data["slug"])
    assert data["url"] == f"http://localhost:5173/s/{data['slug']}"


def test_A17_shared_view_hides_owner(client: TestClient, log_repo: FakeLogRepo) -> None:
    sid = create(client)["id"]
    slug = client.post(f"/api/v1/scenarios/{sid}/share", headers=headers()).json()["slug"]
    response = client.get(f"/api/v1/share/{slug}")
    assert response.status_code == 200
    data = response.json()
    assert "id" not in data and "client_id" not in data
    assert OWNER not in response.text and sid not in response.text
    assert data["result"]["summary"]["monthly_total"] == "1366.04"
    assert [e.source for e in log_repo.entries] == ["share"]


def test_A18_unshare(client: TestClient) -> None:
    sid = create(client)["id"]
    slug = client.post(f"/api/v1/scenarios/{sid}/share", headers=headers()).json()["slug"]
    assert client.delete(f"/api/v1/scenarios/{sid}/share", headers=headers()).status_code == 204
    response = client.get(f"/api/v1/share/{slug}")
    assert response.status_code == 404
    assert response.json()["errors"][0]["message"] == "Odkaz už neplatí."


def test_A19_share_is_idempotent(client: TestClient) -> None:
    sid = create(client)["id"]
    first = client.post(f"/api/v1/scenarios/{sid}/share", headers=headers()).json()["slug"]
    second = client.post(f"/api/v1/scenarios/{sid}/share", headers=headers()).json()["slug"]
    assert first == second


def test_scenarios_return_503_without_database(settings: Settings) -> None:
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        response = c.get("/api/v1/scenarios", headers=headers())
    assert response.status_code == 503
    assert response.json()["errors"][0]["code"] == "db_unavailable"
