from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from calc import LoanInput, validate

from .errors import InputInvalid


class LoanInputSchema(BaseModel):
    """Vstup výpočtu. Sumy môžu prísť ako čísla alebo reťazce."""

    price: Decimal
    down_payment: Decimal
    annual_rate: Decimal
    term_years: Decimal
    first_payment: str = Field(examples=["2026-11"])
    extra_monthly: Decimal = Decimal(0)
    tax_yearly: Decimal = Decimal(0)
    insurance_yearly: Decimal = Decimal(0)
    currency: str = "EUR"

    def to_domain(self) -> LoanInput:
        return LoanInput(**self.model_dump())

    def to_valid_domain(self) -> LoanInput:
        """Prevedie na doménový model a overí ho; pri chybe vyhodí 422."""
        inp = self.to_domain()
        errors = validate(inp)
        if errors:
            raise InputInvalid(errors)
        return inp

    def to_storage(self) -> dict[str, Any]:
        """Vstupy pre stĺpec `scenarios.inputs` (bez meny, sumy ako reťazce)."""
        data = self.model_dump(mode="json", exclude={"currency"})
        data["term_years"] = int(self.term_years)
        return data
