from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, StringConstraints

from calc import monthly_total, validate

from ..db.repos import ScenarioRow
from .loan import LoanInputSchema
from .result import CalculationOut

ScenarioName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class ScenarioCreate(BaseModel):
    name: ScenarioName
    inputs: LoanInputSchema


class ScenarioPatch(BaseModel):
    name: ScenarioName | None = None
    inputs: LoanInputSchema | None = None


def stored_inputs(row: ScenarioRow) -> LoanInputSchema:
    return LoanInputSchema(**row.inputs, currency=row.currency)


class ScenarioOut(BaseModel):
    id: UUID
    name: str
    inputs: LoanInputSchema
    currency: str
    share_slug: str | None
    share_url: str | None
    monthly_total: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: ScenarioRow, public_app_url: str) -> ScenarioOut:
        inputs = stored_inputs(row)
        domain = inputs.to_domain()
        total = None if validate(domain) else f"{monthly_total(domain):.2f}"
        return cls(
            id=row.id,
            name=row.name,
            inputs=inputs,
            currency=row.currency,
            share_slug=row.share_slug,
            share_url=share_url(public_app_url, row.share_slug) if row.share_slug else None,
            monthly_total=total,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class ShareOut(BaseModel):
    slug: str
    url: str


class SharedScenarioOut(BaseModel):
    """Verejný pohľad na zdieľaný scenár – bez id a client_id (F12)."""

    name: str
    inputs: LoanInputSchema
    currency: str
    result: CalculationOut


def share_url(public_app_url: str, slug: str) -> str:
    return f"{public_app_url.rstrip('/')}/s/{slug}"


def storage_changes(patch: ScenarioPatch) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    if patch.name is not None:
        changes["name"] = patch.name
    if patch.inputs is not None:
        changes["inputs"] = patch.inputs.to_storage()
        changes["currency"] = patch.inputs.currency
    return changes
