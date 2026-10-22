"""Ročný súhrn harmonogramu a porovnanie s mimoriadnou splátkou."""

from __future__ import annotations

from .models import Comparison, Payment, ScheduleResult, YearRow


def yearly_rollup(rows: tuple[Payment, ...]) -> tuple[YearRow, ...]:
    """Súčty po kalendárnych rokoch; zostatok je zostatok na konci roka."""
    years: list[YearRow] = []
    for row in rows:
        if years and years[-1].year == row.date.year:
            last = years[-1]
            years[-1] = YearRow(
                year=last.year,
                payment=last.payment + row.payment,
                principal=last.principal + row.principal,
                interest=last.interest + row.interest,
                balance=row.balance,
            )
        else:
            years.append(
                YearRow(row.date.year, row.payment, row.principal, row.interest, row.balance)
            )
    return tuple(years)


def _plural(count: int, one: str, few: str, many: str) -> str:
    if count == 1:
        return one
    if 2 <= count <= 4:
        return few
    return many


def sooner_text(months: int) -> str:
    """Napr. 'o 7 rokov a 6 mesiacov skôr'."""
    years, rest = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} {_plural(years, 'rok', 'roky', 'rokov')}")
    if rest:
        parts.append(f"{rest} {_plural(rest, 'mesiac', 'mesiace', 'mesiacov')}")
    return f"o {' a '.join(parts)} skôr"


def compare(with_extra: ScheduleResult, baseline: ScheduleResult) -> Comparison:
    months = baseline.payments_count - with_extra.payments_count
    return Comparison(
        baseline_payments_count=baseline.payments_count,
        baseline_total_interest=baseline.total_interest,
        interest_saved=baseline.total_interest - with_extra.total_interest,
        months_sooner=months,
        sooner_text=sooner_text(months) if months > 0 else "",
        baseline_balance=tuple(row.balance for row in baseline.rows),
    )
