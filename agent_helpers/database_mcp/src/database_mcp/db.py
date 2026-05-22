from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg import Connection, rows

from database_mcp.config import AppConfig, DatabaseConfig
from database_mcp.connection_url import rewrite_host_port
from database_mcp.sql_guard import first_keyword, validate_read_only_sql
from database_mcp.ssh_tunnel import get_local_bind_port


def _resolve_connection_string(db: DatabaseConfig) -> str:
    if db.ssh is None:
        return db.connection_string
    local_port = get_local_bind_port(db.name, db.ssh)
    return rewrite_host_port(db.connection_string, "127.0.0.1", local_port)


@contextmanager
def _connect(db: DatabaseConfig, *, timeout_seconds: int) -> Iterator[Connection]:
    conn = psycopg.connect(
        _resolve_connection_string(db),
        row_factory=rows.dict_row,
        connect_timeout=timeout_seconds,
    )
    try:
        conn.read_only = True
        with conn.cursor() as cur:
            # SET does not accept bind parameters in PostgreSQL.
            ms = int(timeout_seconds) * 1000
            cur.execute(f"SET statement_timeout = {ms}")
        yield conn
    finally:
        conn.close()


def _rows_to_json(data: list[dict[str, Any]]) -> str:
    return json.dumps(data, indent=2, default=str)


def list_configured_databases(config: AppConfig) -> str:
    lines = [f"Default database: {config.default_database}", ""]
    for name, db in sorted(config.databases.items()):
        desc = db.description or "(no description)"
        if db.ssh is not None:
            ssh = db.ssh
            desc = f"{desc} [SSH {ssh.user}@{ssh.host} -> {ssh.remote_host}:{ssh.remote_port}]"
        lines.append(f"- **{name}**: {desc}")
    return "\n".join(lines)


def list_schemas(config: AppConfig, database: str | None) -> str:
    db = config.get_database(database)
    sql = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
          AND schema_name NOT LIKE 'pg_toast%'
        ORDER BY schema_name
    """
    with _connect(db, timeout_seconds=config.query.timeout_seconds) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(sql)
                rows_data = cur.fetchall()
    return _rows_to_json(rows_data)


def list_tables(config: AppConfig, database: str | None, schema: str = "public") -> str:
    db = config.get_database(database)
    sql = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """
    with _connect(db, timeout_seconds=config.query.timeout_seconds) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(sql, (schema,))
                rows_data = cur.fetchall()
    return _rows_to_json(rows_data)


def describe_table(
    config: AppConfig,
    table: str,
    database: str | None = None,
    schema: str = "public",
) -> str:
    db = config.get_database(database)
    columns_sql = """
        SELECT
            column_name,
            data_type,
            udt_name,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """
    pk_sql = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = %s
          AND tc.table_name = %s
        ORDER BY kcu.ordinal_position
    """
    fk_sql = """
        SELECT
            kcu.column_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = %s
          AND tc.table_name = %s
        ORDER BY kcu.column_name
    """
    indexes_sql = """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = %s AND tablename = %s
        ORDER BY indexname
    """
    with _connect(db, timeout_seconds=config.query.timeout_seconds) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(columns_sql, (schema, table))
                columns = cur.fetchall()
                if not columns:
                    raise ValueError(f"Table {schema}.{table} not found or has no columns")

                cur.execute(pk_sql, (schema, table))
                primary_keys = cur.fetchall()

                cur.execute(fk_sql, (schema, table))
                foreign_keys = cur.fetchall()

                cur.execute(indexes_sql, (schema, table))
                indexes = cur.fetchall()

    result = {
        "schema": schema,
        "table": table,
        "columns": columns,
        "primary_key": primary_keys,
        "foreign_keys": foreign_keys,
        "indexes": indexes,
    }
    return json.dumps(result, indent=2, default=str)


def run_query(
    config: AppConfig,
    sql: str,
    database: str | None = None,
    max_rows: int | None = None,
) -> str:
    db = config.get_database(database)
    safe_sql = validate_read_only_sql(sql)
    limit = min(max_rows or config.query.max_rows, config.query.max_rows)
    if limit < 1:
        raise ValueError("max_rows must be at least 1")

    kind = first_keyword(safe_sql)
    use_wrapper = kind in ("SELECT", "WITH", "TABLE")

    with _connect(db, timeout_seconds=config.query.timeout_seconds) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                if use_wrapper:
                    wrapped = f"SELECT * FROM ({safe_sql}) AS _mcp_subquery LIMIT %s"
                    cur.execute(wrapped, (limit,))
                    rows_data = cur.fetchall()
                    truncated = len(rows_data) >= limit
                else:
                    cur.execute(safe_sql)
                    rows_data = cur.fetchmany(limit)
                    truncated = len(rows_data) >= limit

    payload: dict[str, Any] = {
        "row_count": len(rows_data),
        "truncated": truncated,
        "max_rows": limit,
        "rows": rows_data,
    }
    return json.dumps(payload, indent=2, default=str)
