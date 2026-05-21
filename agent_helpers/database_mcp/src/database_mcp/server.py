from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from database_mcp import db
from database_mcp.config import load_config

mcp = FastMCP(
    "database_mcp",
    instructions=(
        "Read-only access to configured PostgreSQL databases. "
        "Use list_databases first, then list_tables / describe_table to explore schema, "
        "and run_query for SELECT-only SQL. Writes are blocked."
    ),
)

_config = None


def _get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config


@mcp.tool()
def list_databases() -> str:
    """List database aliases configured for this MCP server."""
    return db.list_configured_databases(_get_config())


@mcp.tool()
def list_schemas(database: str | None = None) -> str:
    """List non-system schemas in a database. Omit database to use the default."""
    return db.list_schemas(_get_config(), database)


@mcp.tool()
def list_tables(schema: str = "public", database: str | None = None) -> str:
    """List tables and views in a schema. Omit database to use the default."""
    return db.list_tables(_get_config(), database, schema)


@mcp.tool()
def describe_table(table: str, schema: str = "public", database: str | None = None) -> str:
    """Describe columns, primary keys, foreign keys, and indexes for a table."""
    return db.describe_table(_get_config(), table, database, schema)


@mcp.tool()
def run_query(sql: str, database: str | None = None, max_rows: int | None = None) -> str:
    """
    Run a read-only SQL query (SELECT, WITH, EXPLAIN SELECT, SHOW, or TABLE).
    Results are capped by max_rows (server default applies if omitted).
    """
    return db.run_query(_get_config(), sql, database, max_rows)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
