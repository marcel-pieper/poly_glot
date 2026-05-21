from __future__ import annotations

import stat
from datetime import datetime, timezone
from io import BytesIO

import paramiko

from server_mcp.config import AppConfig, ServerConfig
from server_mcp.ssh import sftp_session


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.2f} GB"


def _format_mtime(ts: float | int | None) -> str:
    if ts is None:
        return "unknown"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _entry_kind(mode: int) -> str:
    if stat.S_ISDIR(mode):
        return "DIR"
    if stat.S_ISLNK(mode):
        return "LINK"
    if stat.S_ISREG(mode):
        return "FILE"
    return "OTHER"


def list_servers(config: AppConfig) -> str:
    lines = [f"Configured servers (default: {config.default_server}):", ""]
    for name in sorted(config.servers):
        server = config.servers[name]
        desc = f" — {server.description}" if server.description else ""
        default_mark = " (default)" if name == config.default_server else ""
        lines.append(f"- {name}{default_mark}: {server.user}@{server.host}:{server.port}{desc}")
    return "\n".join(lines)


def list_directory(
    config: AppConfig,
    server_name: str | None,
    path: str,
    show_hidden: bool = False,
) -> str:
    server = config.get_server(server_name)
    remote_path = path or "/"
    max_entries = config.limits.list_max_entries

    with sftp_session(server) as sftp:
        try:
            entries = sftp.listdir_attr(remote_path)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Directory not found: {remote_path}") from exc
        except OSError as exc:
            raise OSError(f"Cannot list {remote_path}: {exc}") from exc

    entries.sort(key=lambda item: item.filename.lower())
    visible = [e for e in entries if show_hidden or not e.filename.startswith(".")]
    truncated = len(visible) > max_entries
    visible = visible[:max_entries]

    lines = [
        f"Server: {server.name} ({server.host})",
        f"Directory: {remote_path}",
        f"Entries: {len(visible)}{f' (truncated, max {max_entries})' if truncated else ''}",
        "",
    ]
    for entry in visible:
        kind = _entry_kind(entry.st_mode)
        size = _format_size(entry.st_size) if kind == "FILE" else ""
        size_part = f"{size:>10}  " if size else " " * 11
        lines.append(f"[{kind}]  {size_part}{entry.filename}  {_format_mtime(entry.st_mtime)}")

    return "\n".join(lines)


def _is_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    if not data:
        return False
    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
    sample = data[:8192]
    return bool(sample.translate(None, delete=text_chars))


def _decode_line(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw.rstrip("\r\n")
    return raw.decode("utf-8", errors="replace").rstrip("\r\n")


def _read_head_lines(sftp: paramiko.SFTPClient, path: str, count: int) -> list[str]:
    lines: list[str] = []
    with sftp.open(path, "r") as remote_file:
        while len(lines) < count:
            raw = remote_file.readline()
            if not raw:
                break
            lines.append(_decode_line(raw))
    return lines


def _read_tail_lines(sftp: paramiko.SFTPClient, path: str, count: int, file_size: int) -> list[str]:
    if file_size == 0:
        return []
    block_size = 8192
    data = b""
    with sftp.open(path, "r") as remote_file:
        offset = file_size
        while offset > 0 and data.count(b"\n") <= count:
            read_size = min(block_size, offset)
            offset -= read_size
            remote_file.seek(offset)
            data = remote_file.read(read_size) + data
    lines = [_decode_line(raw) for raw in data.splitlines()]
    return lines[-count:]


def _read_line_range(
    sftp: paramiko.SFTPClient,
    path: str,
    offset: int,
    limit: int | None,
) -> tuple[list[str], int, bool]:
    if offset < 1:
        raise ValueError("offset must be >= 1 (1-indexed line number)")

    selected: list[str] = []
    current_line = 0
    truncated = False

    with sftp.open(path, "r") as remote_file:
        while True:
            raw = remote_file.readline()
            if not raw:
                break
            current_line += 1
            if current_line < offset:
                continue
            selected.append(_decode_line(raw))
            if limit is not None and len(selected) >= limit:
                truncated = True
                break

    return selected, current_line, truncated


def read_file(
    config: AppConfig,
    server_name: str | None,
    path: str,
    offset: int | None = None,
    limit: int | None = None,
    preview: bool = False,
) -> str:
    server = config.get_server(server_name)
    limits = config.limits

    with sftp_session(server) as sftp:
        try:
            attrs = sftp.stat(path)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File not found: {path}") from exc

        if not stat.S_ISREG(attrs.st_mode):
            raise ValueError(f"Not a regular file: {path}")

        size = attrs.st_size
        header = [
            f"Server: {server.name} ({server.host})",
            f"Path: {path}",
            f"Size: {_format_size(size)} ({size} bytes)",
            f"Modified: {_format_mtime(attrs.st_mtime)}",
            "",
        ]

        with sftp.open(path, "r") as remote_file:
            sample = remote_file.read(min(size, 8192))

        if _is_binary(sample):
            hex_preview = sample[:256].hex(" ", 1)
            return "\n".join(
                header
                + [
                    "Type: binary (not shown as text)",
                    f"Hex preview (first {min(len(sample), 256)} bytes):",
                    hex_preview,
                ]
            )

        use_preview = preview or (
            offset is None and limit is None and size > limits.auto_preview_above_bytes
        )

        if use_preview:
            head = _read_head_lines(sftp, path, limits.preview_head_lines)
            tail = _read_tail_lines(sftp, path, limits.preview_tail_lines, size)
            lines = header + [
                "Mode: preview",
                f"Showing first {len(head)} and last {len(tail)} lines.",
                "Use offset/limit to read a section, or preview=false with a smaller file.",
                "",
                "--- head ---",
            ]
            for idx, line in enumerate(head, start=1):
                lines.append(f"{idx:6}|{line}")
            if tail:
                lines.extend(["", "... [truncated] ...", "", f"--- tail (last {len(tail)} lines) ---"])
                for line in tail:
                    lines.append(f"       |{line}")
            return "\n".join(lines)

        if offset is not None or limit is not None:
            start = offset or 1
            selected, total_lines, truncated = _read_line_range(sftp, path, start, limit)
            lines = header + [
                f"Mode: section (lines {start}" + (f", limit {limit})" if limit else "-end)"),
                f"Lines returned: {len(selected)}",
            ]
            if truncated:
                lines.append("(section truncated at limit)")
            lines.append("")
            for idx, line in enumerate(selected, start=start):
                lines.append(f"{idx:6}|{line}")
            if not truncated and total_lines > start + len(selected) - 1:
                lines.append("")
                lines.append(f"(file continues; at least {total_lines} lines total)")
            return "\n".join(lines)

        if size > limits.max_read_bytes:
            raise ValueError(
                f"File is {size} bytes, above max_read_bytes ({limits.max_read_bytes}). "
                "Use preview=true or offset/limit to read a section."
            )

        with sftp.open(path, "rb") as remote_file:
            data = remote_file.read(size)
        content_lines = [_decode_line(raw) for raw in data.splitlines()]
        lines = header + ["Mode: full", ""]
        for idx, line in enumerate(content_lines, start=1):
            lines.append(f"{idx:6}|{line}")
        return "\n".join(lines)
