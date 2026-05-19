from __future__ import annotations

import re

import sqlparse
from sqlparse.tokens import Keyword

_FORBIDDEN = frozenset(
    {
        "INSERT",
        "UPDATE",
        "DELETE",
        "MERGE",
        "TRUNCATE",
        "DROP",
        "CREATE",
        "ALTER",
        "GRANT",
        "REVOKE",
        "COPY",
        "CALL",
        "DO",
        "LOCK",
        "VACUUM",
        "ANALYZE",
        "CLUSTER",
        "REINDEX",
        "REFRESH",
        "COMMENT",
        "SECURITY",
        "DISCARD",
        "LOAD",
        "NOTIFY",
        "LISTEN",
        "UNLISTEN",
        "RESET",
        "SET",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "SAVEPOINT",
        "RELEASE",
        "PREPARE",
        "DEALLOCATE",
        "EXECUTE",
    }
)

_ALLOWED_START = frozenset({"SELECT", "WITH", "EXPLAIN", "SHOW", "TABLE"})


def _strip_leading_comments(sql: str) -> str:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return sql.strip()
    return str(parsed[0]).strip()


def _first_keyword(sql: str) -> str:
    for token in sqlparse.parse(sql)[0].flatten():
        if token.ttype in (Keyword.DML, Keyword) and token.value.upper() not in ("AS",):
            return token.value.upper()
    return ""


def _collect_keywords(sql: str) -> set[str]:
    keywords: set[str] = set()
    for token in sqlparse.parse(sql)[0].flatten():
        if token.ttype in (Keyword.DML, Keyword):
            keywords.add(token.value.upper())
    return keywords


def _explain_is_read_only(statement) -> bool:
    """EXPLAIN must be followed by SELECT (or WITH ... SELECT)."""
    seen_explain = False
    for token in statement.flatten():
        val = token.value.upper()
        if token.ttype in (Keyword.DML, Keyword):
            if val == "EXPLAIN":
                seen_explain = True
                continue
            if seen_explain:
                return val in ("SELECT", "WITH")
            return val in _ALLOWED_START
    return False


def _table_command_is_select(statement) -> bool:
    """TABLE foo is shorthand for SELECT * FROM foo."""
    return _first_keyword(str(statement)) == "TABLE"


def validate_read_only_sql(sql: str) -> str:
    cleaned = _strip_leading_comments(sql.strip().rstrip(";"))
    if not cleaned:
        raise ValueError("SQL is empty")

    statements = [s for s in sqlparse.parse(cleaned) if str(s).strip()]
    if len(statements) != 1:
        raise ValueError("Only a single SQL statement is allowed")

    statement = statements[0]
    stmt_type = statement.get_type()
    if stmt_type and stmt_type.upper() not in ("SELECT", "UNKNOWN"):
        raise ValueError(f"Only read-only queries are allowed (got {stmt_type})")

    keywords = _collect_keywords(cleaned)
    forbidden = keywords & _FORBIDDEN
    if forbidden:
        raise ValueError(f"Forbidden SQL keyword(s): {', '.join(sorted(forbidden))}")

    first = _first_keyword(cleaned)
    if first == "EXPLAIN":
        if not _explain_is_read_only(statement):
            raise ValueError("EXPLAIN is only allowed for SELECT queries")
    elif first == "TABLE":
        if not _table_command_is_select(statement):
            raise ValueError("TABLE command is not allowed")
    elif first not in _ALLOWED_START:
        raise ValueError(
            f"Query must start with SELECT, WITH, EXPLAIN, SHOW, or TABLE (got {first or 'unknown'})"
        )

    # Block SELECT ... INTO (creates a table)
    if re.search(r"\bINTO\b", cleaned, re.IGNORECASE) and re.search(
        r"\bSELECT\b", cleaned, re.IGNORECASE
    ):
        raise ValueError("SELECT INTO is not allowed")

    return cleaned


def first_keyword(sql: str) -> str:
    cleaned = _strip_leading_comments(sql.strip().rstrip(";"))
    return _first_keyword(cleaned) if cleaned else ""
