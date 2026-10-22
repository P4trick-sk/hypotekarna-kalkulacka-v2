from __future__ import annotations

from decimal import Decimal

import pytest

from calc import LoanInput


def make_input(
    loan: str = "240000",
    rate: str = "4.5",
    years: str = "30",
    extra: str = "0",
    **overrides: object,
) -> LoanInput:
    """Vstup s cenou = úver + 60 000 a prvou splátkou 2026-11 (ako v 03-test-scenarios)."""
    values: dict[str, object] = {
        "price": Decimal(loan) + Decimal("60000"),
        "down_payment": Decimal("60000"),
        "annual_rate": Decimal(rate),
        "term_years": Decimal(years),
        "first_payment": "2026-11",
        "extra_monthly": Decimal(extra),
    }
    values.update(overrides)
    return LoanInput(**values)  # type: ignore[arg-type]


@pytest.fixture
def default_input() -> LoanInput:
    return LoanInput(
        price=Decimal("300000"),
        down_payment=Decimal("60000"),
        annual_rate=Decimal("4.5"),
        term_years=Decimal("30"),
        first_payment="2026-11",
        tax_yearly=Decimal("1200"),
        insurance_yearly=Decimal("600"),
    )
