from __future__ import annotations

from urllib.parse import quote, unquote, urlsplit, urlunsplit


def rewrite_host_port(connection_string: str, host: str, port: int) -> str:
    """Replace the host and port in a PostgreSQL connection URL."""
    scheme, remainder = _split_postgres_scheme(connection_string)
    parsed = urlsplit(f"//{remainder}")
    if not parsed.hostname:
        raise ValueError(f"Could not parse host from connection string: {connection_string!r}")

    username = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    auth = _format_userinfo(username, password)
    netloc = f"{auth}{host}:{port}" if auth else f"{host}:{port}"

    rebuilt = urlunsplit(("", netloc, parsed.path, parsed.query, parsed.fragment))
    return f"{scheme}://{rebuilt.lstrip('//')}"


def _split_postgres_scheme(connection_string: str) -> tuple[str, str]:
    for prefix in ("postgresql+psycopg://", "postgresql://"):
        if connection_string.startswith(prefix):
            return prefix.removesuffix("://"), connection_string[len(prefix) :]
    raise ValueError(
        "connection_string must start with postgresql:// or postgresql+psycopg://"
    )


def _format_userinfo(username: str | None, password: str | None) -> str:
    if not username:
        return ""
    user = quote(username, safe="")
    if password is None:
        return f"{user}@"
    return f"{user}:{quote(password, safe='')}@"
