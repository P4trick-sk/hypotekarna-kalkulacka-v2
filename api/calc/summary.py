"""Súhrn výsledkov (F4) a hlavná funkcia `calculate`."""

from __future__ import annotations

from decimal import Decimal

from .amortization import ZERO, build_schedule, monthly_payment, round2
from .models import CalculationResult, LoanInput, ScheduleResult, Summary
from .schedule import compare, yearly_rollup

HUNDRED = Decimal(100)


def monthly_escrow(inp: LoanInput) -> Decimal:
    """Daň a poistenie na mesiac; neovplyvňujú zostatok úveru."""
    return round2((inp.tax_yearly + inp.insurance_yearly) / 12)


def monthly_total(inp: LoanInput) -> Decimal:
    """Celková mesačná splátka bez zostavenia harmonogramu (pre zoznam scenárov)."""
    pmt = monthly_payment(inp.loan_amount, inp.annual_rate, inp.payments)
    return pmt + round2(inp.extra_monthly) + monthly_escrow(inp)


def summary(inp: LoanInput, result: ScheduleResult) -> Summary:
    loan = inp.loan_amount
    escrow = monthly_escrow(inp)
    first = result.rows[0]
    first_extra = min(inp.extra_monthly, first.principal)
    total_interest = result.total_interest
    return Summary(
        loan_amount=round2(loan),
        down_payment_pct=round2(inp.down_payment / inp.price * HUNDRED),
        ltv_pct=round2(loan / inp.price * HUNDRED),
        monthly_pi=result.monthly_pi,
        monthly_extra=round2(inp.extra_monthly),
        monthly_escrow=escrow,
        monthly_total=result.monthly_pi + inp.extra_monthly + escrow,
        first_principal=first.principal - first_extra,
        first_interest=first.interest,
        total_interest=total_interest,
        interest_pct_of_loan=round2(total_interest / loan * HUNDRED),
        total_cost=round2(loan + total_interest),
        payoff_date=result.payoff_date,
        payments_count=result.payments_count,
    )


def calculate(inp: LoanInput) -> CalculationResult:
    """Kompletný výpočet pre validovaný vstup (pozri `validation.validate`)."""
    result = build_schedule(inp)
    baseline = None
    if inp.extra_monthly > 0:
        baseline = compare(result, build_schedule(inp, extra=ZERO))
    return CalculationResult(
        summary=summary(inp, result),
        monthly=result.rows,
        yearly=yearly_rollup(result.rows),
        baseline=baseline,
    )
