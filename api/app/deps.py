"""FastAPI závislosti. V testoch sa prepisujú cez `app.dependency_overrides`."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header

from .config import Settings, get_settings
from .db.repos import DatabaseUnavailable, LogRepo, NoopLogRepo, ScenarioRepo
from .schemas.errors import ApiError


def get_log_repo(settings: Annotated[Settings, Depends(get_settings)]) -> LogRepo:
    if not (settings.calc_log_enabled and settings.db_configured):
        return NoopLogRepo()
    from .db.client import SupabaseLogRepo, get_client

    return SupabaseLogRepo(get_client(settings))


def get_scenario_repo(settings: Annotated[Settings, Depends(get_settings)]) -> ScenarioRepo:
    if not settings.db_configured:
        raise DatabaseUnavailable("Supabase nie je nakonfigurovaný (api/.env).")
    from .db.client import SupabaseScenarioRepo, get_client

    return SupabaseScenarioRepo(get_client(settings))


def get_client_id(x_client_id: Annotated[str | None, Header()] = None) -> UUID:
    if not x_client_id:
        raise ApiError(400, "missing_client_id", "Chýba hlavička X-Client-Id.")
    try:
        return UUID(x_client_id)
    except ValueError:
        raise ApiError(400, "invalid_client_id", "X-Client-Id musí byť UUID.") from None


LogRepoDep = Annotated[LogRepo, Depends(get_log_repo)]
ScenarioRepoDep = Annotated[ScenarioRepo, Depends(get_scenario_repo)]
ClientIdDep = Annotated[UUID, Depends(get_client_id)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
