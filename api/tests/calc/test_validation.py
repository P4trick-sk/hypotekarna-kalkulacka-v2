from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from calc import LoanInput, validate

D = Decimal


def codes(inp: LoanInput) -> list[tuple[str, str]]:
    return [(e.field, e.code) for e in validate(inp)]


def test_default_input_is_valid(default_input: LoanInput) -> None:
    assert validate(default_input) == []


def test_V01_price_zero(default_input: LoanInput) -> None:
    assert ("price", "gt_zero") in codes(replace(default_input, price=D(0)))


def test_V02_down_payment_equals_price(default_input: LoanInput) -> None:
    assert codes(replace(default_input, down_payment=D(300000))) == [("down_payment", "gte_price")]


def test_V03_negative_down_payment(default_input: LoanInput) -> None:
    assert codes(replace(default_input, down_payment=D(-1))) == [("down_payment", "negative")]


def test_V04_rate_above_50(default_input: LoanInput) -> None:
    assert codes(replace(default_input, annual_rate=D("50.01"))) == [
        ("annual_rate", "out_of_range")
    ]


@pytest.mark.parametrize(
    "years,code", [("0", "out_of_range"), ("51", "out_of_range"), ("12.5", "not_integer")]
)
def test_V05_term(default_input: LoanInput, years: str, code: str) -> None:
    assert codes(replace(default_input, term_years=D(years))) == [("term_years", code)]


def test_V06_negative_extra(default_input: LoanInput) -> None:
    assert codes(replace(default_input, extra_monthly=D(-10))) == [("extra_monthly", "negative")]


def test_V07_unsupported_currency(default_input: LoanInput) -> None:
    assert codes(replace(default_input, currency="JPY")) == [("currency", "unsupported")]


def test_V08_multiple_errors_in_field_order(default_input: LoanInput) -> None:
    result = codes(replace(default_input, annual_rate=D(60), price=D(0)))
    assert result == [("price", "gt_zero"), ("annual_rate", "out_of_range")]


@pytest.mark.parametrize("value", ["2026-13", "2026-1", "abc", "2026-00"])
def test_V09_invalid_first_payment(default_input: LoanInput, value: str) -> None:
    assert codes(replace(default_input, first_payment=value)) == [("first_payment", "invalid_date")]


def test_messages_are_slovak(default_input: LoanInput) -> None:
    [error] = validate(replace(default_input, down_payment=D(300000)))
    assert error.message == "Akontácia musí byť nižšia ako cena nehnuteľnosti."
