"""CLI: python -m calc --price 300000 --down 60000 --rate 4.5 --years 30 [--extra 200] [--csv]"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from decimal import Decimal

from . import LoanInput, calculate, to_csv, validate
from .models import YearMonth


def next_month() -> str:
    today = date.today()
    return str(YearMonth(today.year, today.month).add_months(1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="calc", description="Hypotekárna kalkulačka")
    parser.add_argument("--price", type=Decimal, required=True)
    parser.add_argument("--down", type=Decimal, required=True)
    parser.add_argument("--rate", type=Decimal, required=True)
    parser.add_argument("--years", type=Decimal, required=True)
    parser.add_argument("--extra", type=Decimal, default=Decimal(0))
    parser.add_argument("--tax", type=Decimal, default=Decimal(0))
    parser.add_argument("--insurance", type=Decimal, default=Decimal(0))
    parser.add_argument("--first", default=next_month(), help="YYYY-MM")
    parser.add_argument("--currency", default="EUR")
    parser.add_argument("--csv", action="store_true", help="vypíše mesačný harmonogram ako CSV")
    args = parser.parse_args(argv)

    inp = LoanInput(
        price=args.price,
        down_payment=args.down,
        annual_rate=args.rate,
        term_years=args.years,
        first_payment=args.first,
        extra_monthly=args.extra,
        tax_yearly=args.tax,
        insurance_yearly=args.insurance,
        currency=args.currency,
    )
    errors = validate(inp)
    if errors:
        for err in errors:
            print(f"{err.field}: {err.message}", file=sys.stderr)
        return 2

    result = calculate(inp)
    if args.csv:
        sys.stdout.write(to_csv(result.monthly))
        return 0

    s = result.summary
    cur = inp.currency
    print(f"Výška úveru:      {s.loan_amount} {cur} (LTV {s.ltv_pct} %)")
    print(f"Mesačná splátka:  {s.monthly_total} {cur}")
    print(f"  istina a úrok:  {s.monthly_pi}")
    print(f"  mimoriadna:     {s.monthly_extra}")
    print(f"  daň a poistenie:{s.monthly_escrow:>9}")
    print(f"Celkové úroky:    {s.total_interest} {cur}")
    print(f"Celková cena:     {s.total_cost} {cur}")
    print(f"Splatené:         {s.payoff_date} ({s.payments_count} splátok)")
    if result.baseline and result.baseline.months_sooner > 0:
        b = result.baseline
        print(f"Ušetrené úroky:   {b.interest_saved} {cur}, {b.sooner_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
