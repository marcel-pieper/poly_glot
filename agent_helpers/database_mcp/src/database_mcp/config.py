from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SshConfig:
    host: str
    user: str
    port: int = 22
    key_file: Path | None = None
    key_passphrase: str | None = None
    remote_host: str = "127.0.0.1"
    remote_port: int = 5433
    local_port: int = 0


@dataclass(frozen=True)
class DatabaseConfig:
    name: str
    description: str
    connection_string: str
    ssh: SshConfig | None = None


@dataclass(frozen=True)
class QueryLimits:
    max_rows: int
    timeout_seconds: int


@dataclass(frozen=True)
class AppConfig:
    default_database: str
    query: QueryLimits
    databases: dict[str, DatabaseConfig]

    def get_database(self, name: str | None) -> DatabaseConfig:
        key = (name or self.default_database).strip()
        if key not in self.databases:
            known = ", ".join(sorted(self.databases))
            raise ValueError(f"Unknown database '{key}'. Configured: {known}")
        return self.databases[key]


def _config_path() -> Path:
    override = os.environ.get("POLYGLOT_DB_MCP_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "config.json"


def _parse_ssh(name: str, raw: dict) -> SshConfig:
    host = raw.get("host")
    user = raw.get("user")
    if not host or not user:
        raise ValueError(f"Database '{name}' ssh config requires host and user")

    key_file = raw.get("key_file")
    key_path = Path(key_file).expanduser() if key_file else None
    if key_path is not None and not key_path.is_file():
        raise FileNotFoundError(f"Database '{name}' ssh key_file not found: {key_path}")
    return SshConfig(
        host=str(host),
        user=str(user),
        port=int(raw.get("port", 22)),
        key_file=key_path,
        key_passphrase=raw.get("key_passphrase"),
        remote_host=str(raw.get("remote_host", "127.0.0.1")),
        remote_port=int(raw.get("remote_port", 5433)),
        local_port=int(raw.get("local_port", 0)),
    )


def load_config() -> AppConfig:
    path = _config_path()
    if not path.is_file():
        example = path.parent / "config.example.json"
        raise FileNotFoundError(
            f"Missing config at {path}. Copy {example} to config.json and edit connection strings."
        )

    raw = json.loads(path.read_text(encoding="utf-8"))
    query_raw = raw.get("query", {})
    query = QueryLimits(
        max_rows=int(query_raw.get("max_rows", 500)),
        timeout_seconds=int(query_raw.get("timeout_seconds", 30)),
    )

    databases: dict[str, DatabaseConfig] = {}
    for name, entry in raw.get("databases", {}).items():
        conn = entry.get("connection_string") or entry.get("url")
        if not conn:
            raise ValueError(f"Database '{name}' is missing connection_string")
        ssh_raw = entry.get("ssh")
        ssh = _parse_ssh(name, ssh_raw) if ssh_raw else None
        databases[name] = DatabaseConfig(
            name=name,
            description=str(entry.get("description", "")),
            connection_string=str(conn),
            ssh=ssh,
        )

    if not databases:
        raise ValueError("No databases configured")

    default_database = str(raw.get("default_database", next(iter(databases))))
    if default_database not in databases:
        raise ValueError(f"default_database '{default_database}' is not in databases")

    return AppConfig(
        default_database=default_database,
        query=query,
        databases=databases,
    )
