"""Jediné miesto, kde API hovorí s databázou: Postgres cez Supabase pooler, rola hk_api."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
from functools import lru_cache
from typing import Any
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool, PoolTimeout

from .repos import DatabaseUnavailable, LogEntry, ScenarioRow, SlugConflict

SCENARIO_COLUMNS = "id, client_id, name, inputs, currency, share_slug, created_at, updated_at"
UPDATABLE = {"name", "inputs", "currency", "share_slug"}


@lru_cache(maxsize=1)
def get_pool(database_url: str) -> ConnectionPool:
    # Pool sa otvára lenivo, aby štart API nepadol pri nedostupnej databáze (A07).
    return ConnectionPool(
        database_url,
        min_size=0,
        max_size=5,
        timeout=5,
        open=True,
        kwargs={"row_factory": dict_row, "connect_timeout": 5},
    )


@contextmanager
def _connection(pool: ConnectionPool) -> Iterator[psycopg.Connection[Any]]:
    """Chyby spojenia prevedie na DatabaseUnavailable (→ 503), duplicitný slug na SlugConflict."""
    try:
        with pool.connection() as conn:
            yield conn
    except psycopg.errors.UniqueViolation as exc:
        raise SlugConflict(str(exc)) from exc
    except (psycopg.OperationalError, PoolTimeout) as exc:
        raise DatabaseUnavailable(str(exc)) from exc


def _row(data: dict[str, Any]) -> ScenarioRow:
    return ScenarioRow(
        id=data["id"],
        client_id=data["client_id"],
        name=data["name"],
        inputs=data["inputs"],
        currency=data["currency"].strip(),
        share_slug=data["share_slug"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _jsonable(value: Any) -> Any:
    return Jsonb(value) if isinstance(value, dict) else value


class PostgresLogRepo:
    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def add(self, entry: LogEntry) -> None:
        data = asdict(entry)
        with _connection(self.pool) as conn:
            conn.execute(
                """
                insert into public.calculation_log
                  (source, inputs, monthly_total, total_interest, payments_count, duration_ms)
                values (%s, %s, %s, %s, %s, %s)
                """,
                (
                    data["source"],
                    Jsonb(data["inputs"]),
                    data["monthly_total"],
                    data["total_interest"],
                    data["payments_count"],
                    data["duration_ms"],
                ),
            )


class PostgresScenarioRepo:
    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def _one(self, query: str, params: tuple[Any, ...]) -> ScenarioRow | None:
        with _connection(self.pool) as conn:
            data = conn.execute(query, params).fetchone()
        return _row(data) if data else None

    def _fetch(self, fn: Callable[[psycopg.Connection[Any]], Any]) -> Any:
        with _connection(self.pool) as conn:
            return fn(conn)

    def ping(self) -> None:
        self._fetch(lambda c: c.execute("select 1").fetchone())

    def list(self, client_id: UUID) -> list[ScenarioRow]:
        rows = self._fetch(
            lambda c: c.execute(
                f"select {SCENARIO_COLUMNS} from public.scenarios "
                "where client_id = %s order by updated_at desc",
                (client_id,),
            ).fetchall()
        )
        return [_row(r) for r in rows]

    def count(self, client_id: UUID) -> int:
        row = self._fetch(
            lambda c: c.execute(
                "select count(*) as n from public.scenarios where client_id = %s", (client_id,)
            ).fetchone()
        )
        return int(row["n"])

    def create(
        self, client_id: UUID, name: str, inputs: dict[str, Any], currency: str
    ) -> ScenarioRow:
        row = self._one(
            "insert into public.scenarios (client_id, name, inputs, currency) "
            f"values (%s, %s, %s, %s) returning {SCENARIO_COLUMNS}",
            (client_id, name, Jsonb(inputs), currency),
        )
        assert row is not None
        return row

    def get(self, client_id: UUID, scenario_id: UUID) -> ScenarioRow | None:
        return self._one(
            f"select {SCENARIO_COLUMNS} from public.scenarios where id = %s and client_id = %s",
            (scenario_id, client_id),
        )

    def update(
        self, client_id: UUID, scenario_id: UUID, changes: dict[str, Any]
    ) -> ScenarioRow | None:
        unknown = set(changes) - UPDATABLE
        if unknown:
            raise ValueError(f"unsupported columns: {unknown}")
        assignments = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder()) for col in changes
        )
        query = sql.SQL(
            "update public.scenarios set {} where id = %s and client_id = %s returning {}"
        ).format(assignments, sql.SQL(SCENARIO_COLUMNS))
        params = (*(_jsonable(v) for v in changes.values()), scenario_id, client_id)
        with _connection(self.pool) as conn:
            data = conn.execute(query, params).fetchone()
        return _row(data) if data else None

    def delete(self, client_id: UUID, scenario_id: UUID) -> bool:
        with _connection(self.pool) as conn:
            cur = conn.execute(
                "delete from public.scenarios where id = %s and client_id = %s",
                (scenario_id, client_id),
            )
            return cur.rowcount > 0

    def get_by_slug(self, slug: str) -> ScenarioRow | None:
        return self._one(
            f"select {SCENARIO_COLUMNS} from public.scenarios where share_slug = %s", (slug,)
        )
