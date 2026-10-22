"""Jediné miesto, kde API hovorí so Supabase (service_role kľúč)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime
from functools import lru_cache
from typing import Any
from uuid import UUID

import httpx
from postgrest.exceptions import APIError
from supabase import Client, create_client

from ..config import Settings
from .repos import DatabaseUnavailable, LogEntry, ScenarioRow, SlugConflict

SCENARIOS = "scenarios"
LOG = "calculation_log"
UNIQUE_VIOLATION = "23505"


@lru_cache(maxsize=1)
def _client(url: str, key: str) -> Client:
    return create_client(url, key)


def get_client(settings: Settings) -> Client:
    return _client(settings.supabase_url, settings.supabase_service_role_key)


def _call[T](fn: Callable[[], T]) -> T:
    """Sieťové chyby a chyby PostgREST prevedie na DatabaseUnavailable (→ 503)."""
    try:
        return fn()
    except APIError as exc:
        if exc.code == UNIQUE_VIOLATION:
            raise SlugConflict(str(exc)) from exc
        raise DatabaseUnavailable(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise DatabaseUnavailable(str(exc)) from exc


def _row(data: Any) -> ScenarioRow:
    return ScenarioRow(
        id=UUID(data["id"]),
        client_id=UUID(data["client_id"]),
        name=data["name"],
        inputs=data["inputs"],
        currency=data["currency"],
        share_slug=data["share_slug"],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


class SupabaseLogRepo:
    def __init__(self, client: Client) -> None:
        self.client = client

    def add(self, entry: LogEntry) -> None:
        _call(lambda: self.client.table(LOG).insert(asdict(entry)).execute())


class SupabaseScenarioRepo:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _owned(self, query: Any, client_id: UUID, scenario_id: UUID) -> Any:
        return query.eq("id", str(scenario_id)).eq("client_id", str(client_id))

    def ping(self) -> None:
        _call(lambda: self.client.table(SCENARIOS).select("id").limit(1).execute())

    def list(self, client_id: UUID) -> list[ScenarioRow]:
        result = _call(
            lambda: (
                self.client.table(SCENARIOS)
                .select("*")
                .eq("client_id", str(client_id))
                .order("updated_at", desc=True)
                .execute()
            )
        )
        return [_row(r) for r in result.data]

    def count(self, client_id: UUID) -> int:
        result = _call(
            lambda: (
                self.client.table(SCENARIOS)
                .select("id", count="exact")  # type: ignore[arg-type]
                .eq("client_id", str(client_id))
                .execute()
            )
        )
        return result.count or 0

    def create(
        self, client_id: UUID, name: str, inputs: dict[str, Any], currency: str
    ) -> ScenarioRow:
        payload: Any = {
            "client_id": str(client_id),
            "name": name,
            "inputs": inputs,
            "currency": currency,
        }
        result = _call(lambda: self.client.table(SCENARIOS).insert(payload).execute())
        return _row(result.data[0])

    def get(self, client_id: UUID, scenario_id: UUID) -> ScenarioRow | None:
        result = _call(
            lambda: self._owned(
                self.client.table(SCENARIOS).select("*"), client_id, scenario_id
            ).execute()
        )
        return _row(result.data[0]) if result.data else None

    def update(
        self, client_id: UUID, scenario_id: UUID, changes: dict[str, Any]
    ) -> ScenarioRow | None:
        result = _call(
            lambda: self._owned(
                self.client.table(SCENARIOS).update(changes), client_id, scenario_id
            ).execute()
        )
        return _row(result.data[0]) if result.data else None

    def delete(self, client_id: UUID, scenario_id: UUID) -> bool:
        result = _call(
            lambda: self._owned(
                self.client.table(SCENARIOS).delete(), client_id, scenario_id
            ).execute()
        )
        return bool(result.data)

    def get_by_slug(self, slug: str) -> ScenarioRow | None:
        result = _call(
            lambda: self.client.table(SCENARIOS).select("*").eq("share_slug", slug).execute()
        )
        return _row(result.data[0]) if result.data else None
