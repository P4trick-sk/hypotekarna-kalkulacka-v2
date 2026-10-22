"""Rozhrania repozitárov. Routery závisia len od týchto protokolov, nie od Supabase."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class LogEntry:
    source: str
    inputs: dict[str, Any]
    monthly_total: str
    total_interest: str
    payments_count: int
    duration_ms: int


@dataclass(frozen=True)
class ScenarioRow:
    id: UUID
    client_id: UUID
    name: str
    inputs: dict[str, Any]
    currency: str
    share_slug: str | None
    created_at: datetime
    updated_at: datetime


class SlugConflict(Exception):
    """Vygenerovaný share_slug už existuje."""


class DatabaseUnavailable(Exception):
    pass


class LogRepo(Protocol):
    def add(self, entry: LogEntry) -> None: ...


class ScenarioRepo(Protocol):
    def ping(self) -> None: ...
    def list(self, client_id: UUID) -> list[ScenarioRow]: ...
    def count(self, client_id: UUID) -> int: ...
    def create(
        self, client_id: UUID, name: str, inputs: dict[str, Any], currency: str
    ) -> ScenarioRow: ...
    def get(self, client_id: UUID, scenario_id: UUID) -> ScenarioRow | None: ...
    def update(
        self, client_id: UUID, scenario_id: UUID, changes: dict[str, Any]
    ) -> ScenarioRow | None: ...
    def delete(self, client_id: UUID, scenario_id: UUID) -> bool: ...
    def get_by_slug(self, slug: str) -> ScenarioRow | None: ...


class NoopLogRepo:
    def add(self, entry: LogEntry) -> None:
        return None
