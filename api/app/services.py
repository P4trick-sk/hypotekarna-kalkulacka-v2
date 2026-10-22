"""Spoločné kroky routerov: výpočet s meraním času a zápis do logu."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from calc import CalculationResult, LoanInput, calculate

from .db.repos import LogEntry, LogRepo
from .schemas.loan import LoanInputSchema

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimedResult:
    result: CalculationResult
    duration_ms: int


def timed_calculate(inp: LoanInput) -> TimedResult:
    start = time.perf_counter()
    result = calculate(inp)
    return TimedResult(result, round((time.perf_counter() - start) * 1000))


def log_entry(source: str, body: LoanInputSchema, timed: TimedResult) -> LogEntry:
    s = timed.result.summary
    return LogEntry(
        source=source,
        inputs=body.model_dump(mode="json"),
        monthly_total=f"{s.monthly_total:.2f}",
        total_interest=f"{s.total_interest:.2f}",
        payments_count=s.payments_count,
        duration_ms=timed.duration_ms,
    )


def write_log(repo: LogRepo, entry: LogEntry) -> None:
    """Spúšťa sa ako BackgroundTask; chyba logu nesmie ovplyvniť výpočet (F13)."""
    try:
        repo.add(entry)
    except Exception:
        logger.exception("Zápis do calculation_log zlyhal")
