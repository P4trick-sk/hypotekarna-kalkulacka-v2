"""Anuitný výpočet a mesačný harmonogram (F3)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .models import LoanInput, Payment, ScheduleResult, YearMonth

CENT = Decimal("0.01")
ZERO = Decimal("0")


def round2(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def monthly_rate(annual_rate: Decimal) -> Decimal:
    return annual_rate / Decimal(100) / Decimal(12)


def monthly_payment(principal: Decimal, annual_rate: Decimal, n: int) -> Decimal:
    """Splátka istiny a úroku: P × r / (1 − (1 + r)^−n); pri 0 % P / n."""
    if n <= 0:
        raise ValueError("number of payments must be positive")
    r = monthly_rate(annual_rate)
    if r == 0:
        return round2(principal / n)
    return round2(principal * r / (1 - (1 + r) ** -n))


def build_schedule(inp: LoanInput, extra: Decimal | None = None) -> ScheduleResult:
    """Mesačný harmonogram pre validovaný vstup.

    `extra` prepíše mimoriadnu splátku zo vstupu (pre porovnanie použi ZERO).
    Posledná splátka uhradí presne zvyšný zostatok, takže rozdiel zo
    zaokrúhlenia splátky nevytvorí splátku navyše.
    """
    extra = inp.extra_monthly if extra is None else extra
    n = inp.payments
    r = monthly_rate(inp.annual_rate)
    pmt = monthly_payment(inp.loan_amount, inp.annual_rate, n)
    start = YearMonth.parse(inp.first_payment)

    balance = inp.loan_amount
    rows: list[Payment] = []
    k = 0
    while balance > 0:
        k += 1
        interest = round2(balance * r)
        principal = pmt - interest + extra
        if principal >= balance or k == n:
            principal = balance
        balance -= principal
        rows.append(
            Payment(
                n=k,
                date=start.add_months(k - 1),
                payment=principal + interest,
                principal=principal,
                interest=interest,
                balance=balance,
            )
        )
    return ScheduleResult(monthly_pi=pmt, rows=tuple(rows))
