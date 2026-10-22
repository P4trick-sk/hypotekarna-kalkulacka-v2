from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db.repos import LogEntry
from app.deps import get_log_repo
from app.main import create_app

DEFAULT_BODY: dict[str, Any] = {
    "price": "300000",
    "down_payment": "60000",
    "annual_rate": "4.5",
    "term_years": 30,
    "first_payment": "2026-11",
    "extra_monthly": "0",
    "tax_yearly": "1200",
    "insurance_yearly": "600",
    "currency": "EUR",
}


class FakeLogRepo:
    def __init__(self, fail: bool = False) -> None:
        self.entries: list[LogEntry] = []
        self.fail = fail

    def add(self, entry: LogEntry) -> None:
        if self.fail:
            raise RuntimeError("db down")
        self.entries.append(entry)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        database_url="",
        cors_origins="http://localhost:5173",
        rate_limit="10000/minute",
    )


@pytest.fixture
def log_repo() -> FakeLogRepo:
    return FakeLogRepo()


@pytest.fixture
def client(settings: Settings, log_repo: FakeLogRepo) -> Iterator[TestClient]:
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_log_repo] = lambda: log_repo
    with TestClient(app) as c:
        yield c
