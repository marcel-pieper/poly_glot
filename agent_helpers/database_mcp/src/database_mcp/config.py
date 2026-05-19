from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseConfig:
    name: str
    description: str
    connection_string: str


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
        databases[name] = DatabaseConfig(
            name=name,
            description=str(entry.get("description", "")),
            connection_string=str(conn),
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
