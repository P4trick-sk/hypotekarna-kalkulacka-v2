from __future__ import annotations

import secrets
import string
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, status

from ..db.repos import ScenarioRow, SlugConflict
from ..deps import ClientIdDep, LogRepoDep, ScenarioRepoDep, SettingsDep
from ..schemas.errors import ApiError, not_found
from ..schemas.result import CalculationOut
from ..schemas.scenario import (
    ScenarioCreate,
    ScenarioOut,
    ScenarioPatch,
    SharedScenarioOut,
    ShareOut,
    share_url,
    storage_changes,
    stored_inputs,
)
from ..services import log_entry, timed_calculate, write_log

router = APIRouter(tags=["scenáre"])

MAX_SCENARIOS = 50
SLUG_ALPHABET = string.ascii_letters + string.digits
SLUG_LENGTH = 10
SLUG_ATTEMPTS = 3


def new_slug() -> str:
    return "".join(secrets.choice(SLUG_ALPHABET) for _ in range(SLUG_LENGTH))


def _scenario_not_found() -> ApiError:
    # Cudzí aj neexistujúci scenár vracajú rovnakú odpoveď (04-review R2).
    return not_found("Scenár sa nenašiel.")


def _owned(repo: ScenarioRepoDep, client_id: UUID, scenario_id: UUID) -> ScenarioRow:
    row = repo.get(client_id, scenario_id)
    if row is None:
        raise _scenario_not_found()
    return row


@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(
    client_id: ClientIdDep, repo: ScenarioRepoDep, settings: SettingsDep
) -> list[ScenarioOut]:
    return [ScenarioOut.from_row(row, settings.public_app_url) for row in repo.list(client_id)]


@router.post("/scenarios", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
def create_scenario(
    body: ScenarioCreate, client_id: ClientIdDep, repo: ScenarioRepoDep, settings: SettingsDep
) -> ScenarioOut:
    body.inputs.to_valid_domain()
    if repo.count(client_id) >= MAX_SCENARIOS:
        raise ApiError(
            409, "limit_reached", f"Môžeš mať najviac {MAX_SCENARIOS} uložených scenárov."
        )
    row = repo.create(client_id, body.name, body.inputs.to_storage(), body.inputs.currency)
    return ScenarioOut.from_row(row, settings.public_app_url)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioOut)
def get_scenario(
    scenario_id: UUID, client_id: ClientIdDep, repo: ScenarioRepoDep, settings: SettingsDep
) -> ScenarioOut:
    return ScenarioOut.from_row(_owned(repo, client_id, scenario_id), settings.public_app_url)


@router.patch("/scenarios/{scenario_id}", response_model=ScenarioOut)
def update_scenario(
    scenario_id: UUID,
    body: ScenarioPatch,
    client_id: ClientIdDep,
    repo: ScenarioRepoDep,
    settings: SettingsDep,
) -> ScenarioOut:
    if body.inputs is not None:
        body.inputs.to_valid_domain()
    changes = storage_changes(body)
    row = (
        repo.update(client_id, scenario_id, changes)
        if changes
        else repo.get(client_id, scenario_id)
    )
    if row is None:
        raise _scenario_not_found()
    return ScenarioOut.from_row(row, settings.public_app_url)


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: UUID, client_id: ClientIdDep, repo: ScenarioRepoDep) -> None:
    if not repo.delete(client_id, scenario_id):
        raise _scenario_not_found()


@router.post("/scenarios/{scenario_id}/share", response_model=ShareOut)
def share_scenario(
    scenario_id: UUID, client_id: ClientIdDep, repo: ScenarioRepoDep, settings: SettingsDep
) -> ShareOut:
    row = _owned(repo, client_id, scenario_id)
    slug = row.share_slug
    attempts = 0
    while slug is None:
        attempts += 1
        try:
            updated = repo.update(client_id, scenario_id, {"share_slug": new_slug()})
        except SlugConflict:
            if attempts >= SLUG_ATTEMPTS:
                raise
            continue
        if updated is None:
            raise _scenario_not_found()
        slug = updated.share_slug
    return ShareOut(slug=slug, url=share_url(settings.public_app_url, slug))


@router.delete("/scenarios/{scenario_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def unshare_scenario(scenario_id: UUID, client_id: ClientIdDep, repo: ScenarioRepoDep) -> None:
    if repo.update(client_id, scenario_id, {"share_slug": None}) is None:
        raise _scenario_not_found()


@router.get("/share/{slug}", response_model=SharedScenarioOut)
def get_shared(
    slug: str, repo: ScenarioRepoDep, log_repo: LogRepoDep, background: BackgroundTasks
) -> SharedScenarioOut:
    row = repo.get_by_slug(slug) if len(slug) == SLUG_LENGTH and slug.isalnum() else None
    if row is None:
        raise not_found("Odkaz už neplatí.")
    inputs = stored_inputs(row)
    timed = timed_calculate(inputs.to_valid_domain())
    background.add_task(write_log, log_repo, log_entry("share", inputs, timed))
    return SharedScenarioOut(
        name=row.name,
        inputs=inputs,
        currency=row.currency,
        result=CalculationOut.from_domain(timed.result),
    )
