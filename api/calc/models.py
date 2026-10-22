"""Doménové modely výpočtovej logiky. Nemenné dataclasses, peniaze v Decimal."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

SUPPORTED_CURRENCIES = ("EUR", "USD", "GBP", "CZK", "CHF", "PLN")


@dataclass(frozen=True)
class YearMonth:
    year: int
    month: int

    @classmethod
    def parse(cls, value: str) -> YearMonth:
        """Prečíta 'YYYY-MM'. Pri neplatnom vstupe vyhodí ValueError."""
        parts = value.split("-")
        if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
            raise ValueError(f"invalid year-month: {value!r}")
        year, month = int(parts[0]), int(parts[1])
        if not 1 <= month <= 12:
            raise ValueError(f"invalid month: {value!r}")
        return cls(year, month)

    def add_months(self, months: int) -> YearMonth:
        index = self.year * 12 + (self.month - 1) + months
        return YearMonth(index // 12, index % 12 + 1)

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


@dataclass(frozen=True)
class LoanInput:
    price: Decimal
    down_payment: Decimal
    annual_rate: Decimal
    # Decimal, aby validácia vedela odhaliť necelé roky (12.5).
    term_years: Decimal
    # 'YYYY-MM' – parsuje sa až po validácii.
    first_payment: str
    extra_monthly: Decimal = Decimal("0")
    tax_yearly: Decimal = Decimal("0")
    insurance_yearly: Decimal = Decimal("0")
    currency: str = "EUR"

    @property
    def loan_amount(self) -> Decimal:
        return self.price - self.down_payment

    @property
    def payments(self) -> int:
        return int(self.term_years) * 12


@dataclass(frozen=True)
class ValidationError:
    field: str
    code: str
    message: str


@dataclass(frozen=True)
class Payment:
    n: int
    date: YearMonth
    payment: Decimal
    principal: Decimal
    interest: Decimal
    balance: Decimal


@dataclass(frozen=True)
class YearRow:
    year: int
    payment: Decimal
    principal: Decimal
    interest: Decimal
    balance: Decimal


@dataclass(frozen=True)
class ScheduleResult:
    monthly_pi: Decimal
    rows: tuple[Payment, ...]

    @property
    def total_interest(self) -> Decimal:
        return sum((p.interest for p in self.rows), Decimal("0"))

    @property
    def payments_count(self) -> int:
        return len(self.rows)

    @property
    def payoff_date(self) -> YearMonth:
        return self.rows[-1].date


@dataclass(frozen=True)
class Comparison:
    """Porovnanie harmonogramu s mimoriadnou splátkou voči štandardnému."""

    baseline_payments_count: int
    baseline_total_interest: Decimal
    interest_saved: Decimal
    months_sooner: int
    sooner_text: str
    baseline_balance: tuple[Decimal, ...]


@dataclass(frozen=True)
class Summary:
    loan_amount: Decimal
    down_payment_pct: Decimal
    ltv_pct: Decimal
    monthly_pi: Decimal
    monthly_extra: Decimal
    monthly_escrow: Decimal
    monthly_total: Decimal
    first_principal: Decimal
    first_interest: Decimal
    total_interest: Decimal
    interest_pct_of_loan: Decimal
    total_cost: Decimal
    payoff_date: YearMonth
    payments_count: int


@dataclass(frozen=True)
class CalculationResult:
    summary: Summary
    monthly: tuple[Payment, ...]
    yearly: tuple[YearRow, ...]
    baseline: Comparison | None = field(default=None)
