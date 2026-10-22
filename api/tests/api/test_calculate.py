from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.deps import get_log_repo

from .conftest import DEFAULT_BODY, FakeLogRepo


def body(**overrides: Any) -> dict[str, Any]:
    return {**DEFAULT_BODY, **overrides}


def test_A01_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_A02_calculate_defaults(client: TestClient) -> None:
    response = client.post("/api/v1/calculate", json=DEFAULT_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["monthly_total"] == "1366.04"
    assert data["summary"]["payoff_date"] == "2056-10"
    assert len(data["monthly"]) == 360
    assert data["monthly"][0] == {
        "n": 1,
        "date": "2026-11",
        "payment": "1216.04",
        "principal": "316.04",
        "interest": "900.00",
        "balance": "239683.96",
    }
    assert data["baseline"] is None


def test_A02_calculate_with_extra_has_baseline(client: TestClient) -> None:
    data = client.post("/api/v1/calculate", json=body(extra_monthly="200")).json()
    assert data["baseline"]["months_sooner"] == 90
    assert data["baseline"]["interest_saved"] == "55889.72"
    assert len(data["baseline"]["balance"]) == 360


def test_A03_invalid_input_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/calculate", json=body(down_payment="300000"))
    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "gte_price"


def test_A03_unparsable_number_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/calculate", json=body(price="abc"))
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "price"


def _walk(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return [x for v in value.values() for x in _walk(v)]
    if isinstance(value, list):
        return [x for v in value for x in _walk(v)]
    return [value]


def test_A04_money_is_serialized_as_strings(client: TestClient) -> None:
    data = client.post("/api/v1/calculate", json=body(extra_monthly="150")).json()
    assert not any(isinstance(v, float) for v in _walk(data))


def test_A05_log_written_without_client_id(client: TestClient, log_repo: FakeLogRepo) -> None:
    client.post(
        "/api/v1/calculate",
        json=DEFAULT_BODY,
        headers={"X-Log": "1", "X-Client-Id": "6f1c1c1e-0000-4000-8000-000000000000"},
    )
    assert len(log_repo.entries) == 1
    entry = log_repo.entries[0]
    assert entry.source == "live"
    assert entry.monthly_total == "1366.04"
    assert "client_id" not in entry.inputs


def test_A05_log_skipped_with_x_log_0(client: TestClient, log_repo: FakeLogRepo) -> None:
    client.post("/api/v1/calculate", json=DEFAULT_BODY, headers={"X-Log": "0"})
    assert log_repo.entries == []


def test_A06_log_failure_does_not_break_calculation(client: TestClient) -> None:
    client.app.dependency_overrides[get_log_repo] = lambda: FakeLogRepo(fail=True)  # type: ignore[attr-defined]
    response = client.post("/api/v1/calculate", json=DEFAULT_BODY)
    assert response.status_code == 200
    assert response.json()["summary"]["monthly_total"] == "1366.04"


def test_A07_calculate_works_without_database(client: TestClient) -> None:
    # settings fixture nemá Supabase nakonfigurovaný
    assert client.get("/api/v1/health").json()["db"] == "not_configured"
    assert client.post("/api/v1/calculate", json=DEFAULT_BODY).status_code == 200


def test_A08_export_csv(client: TestClient) -> None:
    response = client.post("/api/v1/export/csv", json=body(currency="CZK"))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="mortgage-schedule-czk.csv"'
    )
    assert len(response.text.splitlines()) == 361


def test_A20_cors_rejects_unknown_origin(client: TestClient) -> None:
    allowed = client.options(
        "/api/v1/calculate",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    denied = client.options(
        "/api/v1/calculate",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in denied.headers
