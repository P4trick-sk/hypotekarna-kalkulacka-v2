from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Header
from fastapi.responses import Response

from calc import csv_filename, to_csv

from ..deps import LogRepoDep
from ..schemas.loan import LoanInputSchema
from ..schemas.result import CalculationOut
from ..services import log_entry, timed_calculate, write_log

router = APIRouter(tags=["výpočet"])


@router.post("/calculate", response_model=CalculationOut)
def calculate_endpoint(
    body: LoanInputSchema,
    background: BackgroundTasks,
    log_repo: LogRepoDep,
    x_log: Annotated[Literal["0", "1"], Header()] = "1",
    x_log_source: Annotated[Literal["live", "scenario"], Header()] = "live",
) -> CalculationOut:
    timed = timed_calculate(body.to_valid_domain())
    if x_log == "1":
        background.add_task(write_log, log_repo, log_entry(x_log_source, body, timed))
    return CalculationOut.from_domain(timed.result)


@router.post("/export/csv", response_class=Response)
def export_csv(body: LoanInputSchema) -> Response:
    inp = body.to_valid_domain()
    result = timed_calculate(inp).result
    return Response(
        content=to_csv(result.monthly),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{csv_filename(inp.currency)}"'},
    )
