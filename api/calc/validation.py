"""Autoritatívna validácia vstupov (F2). Kódy chýb zdieľa aj frontend."""

from __future__ import annotations

from decimal import Decimal

from .models import SUPPORTED_CURRENCIES, LoanInput, ValidationError, YearMonth

MAX_RATE = Decimal("50")
MIN_TERM, MAX_TERM = 1, 50

FIELD_ORDER = (
    "price",
    "down_payment",
    "annual_rate",
    "term_years",
    "first_payment",
    "extra_monthly",
    "tax_yearly",
    "insurance_yearly",
    "currency",
)

MESSAGES = {
    ("price", "gt_zero"): "Cena nehnuteľnosti musí byť väčšia ako 0.",
    ("down_payment", "negative"): "Akontácia nemôže byť záporná.",
    ("down_payment", "gte_price"): "Akontácia musí byť nižšia ako cena nehnuteľnosti.",
    ("annual_rate", "out_of_range"): "Úroková sadzba musí byť od 0 do 50 %.",
    ("term_years", "not_integer"): "Doba splatnosti musí byť v celých rokoch.",
    ("term_years", "out_of_range"): "Doba splatnosti musí byť od 1 do 50 rokov.",
    ("first_payment", "invalid_date"): "Prvá splátka musí byť platný mesiac a rok.",
    ("extra_monthly", "negative"): "Mimoriadna splátka nemôže byť záporná.",
    ("tax_yearly", "negative"): "Daň z nehnuteľnosti nemôže byť záporná.",
    ("insurance_yearly", "negative"): "Poistenie nemôže byť záporné.",
    ("currency", "unsupported"): "Táto mena nie je podporovaná.",
}


def _error(field: str, code: str) -> ValidationError:
    return ValidationError(field, code, MESSAGES[(field, code)])


def validate(inp: LoanInput) -> list[ValidationError]:
    """Vráti všetky chyby v poradí polí z F1; prázdny zoznam = vstup je platný."""
    errors: list[ValidationError] = []

    price_ok = inp.price > 0
    if not price_ok:
        errors.append(_error("price", "gt_zero"))

    if inp.down_payment < 0:
        errors.append(_error("down_payment", "negative"))
    elif price_ok and inp.down_payment >= inp.price:
        errors.append(_error("down_payment", "gte_price"))

    if not 0 <= inp.annual_rate <= MAX_RATE:
        errors.append(_error("annual_rate", "out_of_range"))

    if inp.term_years != inp.term_years.to_integral_value():
        errors.append(_error("term_years", "not_integer"))
    elif not MIN_TERM <= inp.term_years <= MAX_TERM:
        errors.append(_error("term_years", "out_of_range"))

    try:
        YearMonth.parse(inp.first_payment)
    except ValueError:
        errors.append(_error("first_payment", "invalid_date"))

    for name in ("extra_monthly", "tax_yearly", "insurance_yearly"):
        if getattr(inp, name) < 0:
            errors.append(_error(name, "negative"))

    if inp.currency not in SUPPORTED_CURRENCIES:
        errors.append(_error("currency", "unsupported"))

    return errors
