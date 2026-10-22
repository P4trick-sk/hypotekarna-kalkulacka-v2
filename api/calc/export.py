"""CSV export mesačného harmonogramu (F6)."""

from __future__ import annotations

import csv
import io

from .models import Payment

HEADER = ("payment_no", "date", "payment", "principal", "interest", "balance")


def to_csv(rows: tuple[Payment, ...]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(HEADER)
    for row in rows:
        writer.writerow(
            (row.n, str(row.date), row.payment, row.principal, row.interest, row.balance)
        )
    return buffer.getvalue()


def csv_filename(currency: str) -> str:
    return f"mortgage-schedule-{currency.lower()}.csv"
