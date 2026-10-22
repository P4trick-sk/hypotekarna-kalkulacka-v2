"""Odpoveď výpočtu. Sumy sa serializujú ako reťazce s dvoma desatinnými miestami."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

from calc import CalculationResult

Money = Annotated[Decimal, PlainSerializer(lambda v: f"{v:.2f}", return_type=str)]


class SummaryOut(BaseModel):
    loan_amount: Money
    down_payment_pct: Money
    ltv_pct: Money
    monthly_pi: Money
    monthly_extra: Money
    monthly_escrow: Money
    monthly_total: Money
    first_principal: Money
    first_interest: Money
    total_interest: Money
    interest_pct_of_loan: Money
    total_cost: Money
    payoff_date: str
    payments_count: int


class PaymentOut(BaseModel):
    n: int
    date: str
    payment: Money
    principal: Money
    interest: Money
    balance: Money


class YearOut(BaseModel):
    year: int
    payment: Money
    principal: Money
    interest: Money
    balance: Money


class BaselineOut(BaseModel):
    payments_count: int
    total_interest: Money
    interest_saved: Money
    months_sooner: int
    sooner_text: str
    balance: list[Money]


class CalculationOut(BaseModel):
    summary: SummaryOut
    monthly: list[PaymentOut]
    yearly: list[YearOut]
    baseline: BaselineOut | None

    @classmethod
    def from_domain(cls, result: CalculationResult) -> CalculationOut:
        s = result.summary
        b = result.baseline
        return cls(
            summary=SummaryOut(
                **{
                    name: getattr(s, name)
                    for name in SummaryOut.model_fields
                    if name != "payoff_date"
                },
                payoff_date=str(s.payoff_date),
            ),
            monthly=[
                PaymentOut(
                    n=p.n,
                    date=str(p.date),
                    payment=p.payment,
                    principal=p.principal,
                    interest=p.interest,
                    balance=p.balance,
                )
                for p in result.monthly
            ],
            yearly=[
                YearOut(
                    year=y.year,
                    payment=y.payment,
                    principal=y.principal,
                    interest=y.interest,
                    balance=y.balance,
                )
                for y in result.yearly
            ],
            baseline=None
            if b is None
            else BaselineOut(
                payments_count=b.baseline_payments_count,
                total_interest=b.baseline_total_interest,
                interest_saved=b.interest_saved,
                months_sooner=b.months_sooner,
                sooner_text=b.sooner_text,
                balance=list(b.baseline_balance),
            ),
        )
