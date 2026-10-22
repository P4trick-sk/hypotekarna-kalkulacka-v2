from __future__ import annotations

import time
from decimal import Decimal

import pytest

from calc import build_schedule, calculate, to_csv
from calc.schedule import sooner_text, yearly_rollup

from .conftest import make_input

D = Decimal

GOLDEN = [
    # id, úver, sadzba, roky, mimoriadna, splátka, celkové úroky, počet, posledná splátka
    ("C01", "240000", "4.5", "30", "0", "1216.04", "197778.11", 360, "1219.75"),
    ("C02", "240000", "4.5", "30", "200", "1216.04", "141888.39", 270, "973.63"),
    ("C03", "120000", "0", "10", "0", "1000.00", "0.00", 120, "1000.00"),
    ("C04", "100000", "3", "20", "0", "554.60", "33103.24", 240, "553.84"),
    ("C05", "240000", "4.5", "30", "3000", "1216.04", "30473.97", 65, "647.41"),
]


@pytest.mark.parametrize(
    "case_id,loan,rate,years,extra,pmt,interest,count,last", GOLDEN, ids=[g[0] for g in GOLDEN]
)
def test_C01_C05_golden_values(
    case_id: str,
    loan: str,
    rate: str,
    years: str,
    extra: str,
    pmt: str,
    interest: str,
    count: int,
    last: str,
) -> None:
    result = build_schedule(make_input(loan, rate, years, extra))
    assert result.monthly_pi == D(pmt)
    assert result.total_interest == D(interest)
    assert result.payments_count == count
    assert result.rows[-1].payment == D(last)


def test_C06_first_row() -> None:
    first = build_schedule(make_input()).rows[0]
    assert (first.interest, first.principal, first.balance) == (
        D("900.00"),
        D("316.04"),
        D("239683.96"),
    )


def test_C07_payoff_date() -> None:
    assert str(build_schedule(make_input()).payoff_date) == "2056-10"


def test_C08_comparison_with_extra_200() -> None:
    baseline = calculate(make_input(extra="200")).baseline
    assert baseline is not None
    assert baseline.interest_saved == D("55889.72")
    assert baseline.months_sooner == 90
    assert baseline.sooner_text == "o 7 rokov a 6 mesiacov skôr"


def test_C09_comparison_with_extra_3000() -> None:
    baseline = calculate(make_input(extra="3000")).baseline
    assert baseline is not None
    assert baseline.months_sooner == 295
    assert baseline.sooner_text == "o 24 rokov a 7 mesiacov skôr"


@pytest.mark.parametrize("case", GOLDEN, ids=[g[0] for g in GOLDEN])
def test_C10_balance_zero_and_principal_sums_to_loan(case: tuple) -> None:
    _, loan, rate, years, extra, *_ = case
    result = build_schedule(make_input(loan, rate, years, extra))
    assert result.rows[-1].balance == D("0.00")
    assert sum(r.principal for r in result.rows) == D(loan)


@pytest.mark.parametrize("case", GOLDEN, ids=[g[0] for g in GOLDEN])
def test_C11_no_negative_values(case: tuple) -> None:
    _, loan, rate, years, extra, *_ = case
    for row in build_schedule(make_input(loan, rate, years, extra)).rows:
        assert row.principal >= 0 and row.balance >= 0 and row.interest >= 0


def test_C12_escrow_does_not_change_schedule() -> None:
    plain = calculate(make_input())
    with_escrow = calculate(make_input(tax_yearly=D("1200"), insurance_yearly=D("600")))
    assert with_escrow.summary.monthly_escrow == D("150.00")
    assert with_escrow.summary.monthly_total == D("1366.04")
    assert with_escrow.monthly == plain.monthly


def test_C13_yearly_rollup() -> None:
    result = build_schedule(make_input())
    years = yearly_rollup(result.rows)
    assert years[0].year == 2026 and years[-1].year == 2056
    counts = {y: sum(1 for r in result.rows if r.date.year == y) for y in (2026, 2056)}
    assert counts == {2026: 2, 2056: 10}
    assert sum(y.interest for y in years) == result.total_interest
    assert years[-1].balance == 0


def test_C14_csv_export() -> None:
    lines = to_csv(build_schedule(make_input("120000", "0", "10")).rows).splitlines()
    assert len(lines) == 121
    assert lines[0] == "payment_no,date,payment,principal,interest,balance"
    assert lines[1] == "1,2026-11,1000.00,1000.00,0.00,119000.00"


def test_C15_one_year_at_50_percent() -> None:
    result = build_schedule(make_input(rate="50", years="1"))
    assert result.payments_count == 12
    assert result.rows[-1].balance == 0


def test_C16_performance_50_years() -> None:
    inp = make_input(loan="1940000", years="50", extra="100")
    start = time.perf_counter()
    calculate(inp)
    assert time.perf_counter() - start < 0.2


@pytest.mark.parametrize(
    "months,text",
    [
        (1, "o 1 mesiac skôr"),
        (3, "o 3 mesiace skôr"),
        (12, "o 1 rok skôr"),
        (51, "o 4 roky a 3 mesiace skôr"),
    ],
)
def test_sooner_text_plurals(months: int, text: str) -> None:
    assert sooner_text(months) == text


def test_no_baseline_without_extra(default_input) -> None:  # type: ignore[no-untyped-def]
    assert calculate(default_input).baseline is None
