from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ReadLimits:
    max_read_bytes: int
    auto_preview_above_bytes: int
    preview_head_lines: int
    preview_tail_lines: int
    list_max_entries: int


@dataclass(frozen=True)
class ServerConfig:
    name: str
    description: str
    host: str
    port: int
    user: str
    key_file: Path | None
    key_passphrase: str | None
    connect_timeout_seconds: int


@dataclass(frozen=True)
class AppConfig:
    default_server: str
    limits: ReadLimits
    servers: dict[str, ServerConfig]

    def get_server(self, name: str | None) -> ServerConfig:
        key = (name or self.default_server).strip()
        if key not in self.servers:
            known = ", ".join(sorted(self.servers))
            raise ValueError(f"Unknown server '{key}'. Configured: {known}")
        return self.servers[key]


def _config_path() -> Path:
    override = os.environ.get("POLYGLOT_SERVER_MCP_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "config.yaml"


def _require_str(entry: dict, key: str, server_name: str) -> str:
    value = entry.get(key)
    if not value or not str(value).strip():
        raise ValueError(f"Server '{server_name}' is missing required field '{key}'")
    return str(value).strip()


def load_config() -> AppConfig:
    path = _config_path()
    if not path.is_file():
        example = path.parent / "config.example.yaml"
        raise FileNotFoundError(
            f"Missing config at {path}. Copy {example} to config.yaml and edit SSH settings."
        )

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    limits_raw = raw.get("limits", {})
    limits = ReadLimits(
        max_read_bytes=int(limits_raw.get("max_read_bytes", 1_048_576)),
        auto_preview_above_bytes=int(limits_raw.get("auto_preview_above_bytes", 65_536)),
        preview_head_lines=int(limits_raw.get("preview_head_lines", 50)),
        preview_tail_lines=int(limits_raw.get("preview_tail_lines", 20)),
        list_max_entries=int(limits_raw.get("list_max_entries", 500)),
    )

    servers: dict[str, ServerConfig] = {}
    for name, entry in (raw.get("servers") or {}).items():
        if not isinstance(entry, dict):
            raise ValueError(f"Server '{name}' must be a mapping")
        key_file_raw = entry.get("key_file")
        key_file = Path(str(key_file_raw)).expanduser() if key_file_raw else None
        passphrase_raw = entry.get("key_passphrase")
        servers[name] = ServerConfig(
            name=name,
            description=str(entry.get("description", "")),
            host=_require_str(entry, "host", name),
            port=int(entry.get("port", 22)),
            user=_require_str(entry, "user", name),
            key_file=key_file,
            key_passphrase=str(passphrase_raw) if passphrase_raw else None,
            connect_timeout_seconds=int(entry.get("connect_timeout_seconds", 20)),
        )

    if not servers:
        raise ValueError("No servers configured")

    default_server = str(raw.get("default_server", next(iter(servers))))
    if default_server not in servers:
        raise ValueError(f"default_server '{default_server}' is not in servers")

    return AppConfig(default_server=default_server, limits=limits, servers=servers)
