from __future__ import annotations

from datetime import datetime, timezone

from server_mcp.config import AppConfig, ServerConfig
from server_mcp.nginx_guard import (
    NGINX_SITES_AVAILABLE,
    NGINX_SITES_ENABLED,
    site_available_path,
    site_enabled_path,
    validate_site_name,
)
from server_mcp.remote_exec import run_command
from server_mcp.ssh import sftp_session


def _server(config: AppConfig, server_name: str | None) -> ServerConfig:
    return config.get_server(server_name)


def nginx_list_sites(config: AppConfig, server_name: str | None) -> str:
    server = _server(config, server_name)
    available = run_command(server, f"ls -la {NGINX_SITES_AVAILABLE}")
    enabled = run_command(server, f"ls -la {NGINX_SITES_ENABLED}")
    return "\n\n".join(
        [
            f"Server: {server.name} ({server.host})",
            "--- sites-available ---",
            available.format(),
            "--- sites-enabled ---",
            enabled.format(),
        ]
    )


def nginx_test_config(config: AppConfig, server_name: str | None) -> str:
    server = _server(config, server_name)
    result = run_command(server, "nginx -t")
    header = f"Server: {server.name} ({server.host})\n"
    if result.exit_code == 0:
        return header + "nginx -t: OK\n\n" + result.format()
    return header + "nginx -t: FAILED\n\n" + result.format()


def nginx_write_site(
    config: AppConfig,
    server_name: str | None,
    site_name: str,
    content: str,
    *,
    backup: bool = True,
) -> str:
    server = _server(config, server_name)
    name = validate_site_name(site_name)
    path = site_available_path(name)
    lines = [f"Server: {server.name} ({server.host})", f"Site: {name}", f"Path: {path}"]

    with sftp_session(server) as sftp:
        if backup:
            try:
                sftp.stat(path)
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                backup_path = f"{path}.bak.{stamp}"
                run_command(server, f"cp {path} {backup_path}")
                lines.append(f"Backup: {backup_path}")
            except FileNotFoundError:
                lines.append("Backup: skipped (no existing file)")

        data = content.encode("utf-8")
        with sftp.file(path, "w") as remote_file:
            remote_file.write(data)

    lines.append(f"Wrote: {len(data)} bytes")
    lines.append("")
    lines.append("Next: nginx_test_config, then nginx_enable_site (if new), then nginx_apply.")
    return "\n".join(lines)


def nginx_enable_site(config: AppConfig, server_name: str | None, site_name: str) -> str:
    server = _server(config, server_name)
    name = validate_site_name(site_name)
    available = site_available_path(name)
    enabled = site_enabled_path(name)

    check = run_command(server, f"test -f {available}")
    if check.exit_code != 0:
        raise FileNotFoundError(f"Site file not found: {available}")

    result = run_command(server, f"ln -sf {available} {enabled}")
    lines = [
        f"Server: {server.name} ({server.host})",
        f"Enabled site: {name}",
        f"Symlink: {enabled} -> {available}",
        "",
        result.format(),
    ]
    if result.exit_code != 0:
        raise RuntimeError("\n".join(lines))
    lines.append("")
    lines.append("Run nginx_test_config, then nginx_apply to load changes.")
    return "\n".join(lines)


def nginx_disable_site(config: AppConfig, server_name: str | None, site_name: str) -> str:
    server = _server(config, server_name)
    name = validate_site_name(site_name)
    enabled = site_enabled_path(name)
    result = run_command(server, f"rm -f {enabled}")
    lines = [
        f"Server: {server.name} ({server.host})",
        f"Disabled site: {name}",
        f"Removed: {enabled}",
        "",
        result.format(),
    ]
    if result.exit_code != 0:
        raise RuntimeError("\n".join(lines))
    lines.append("")
    lines.append("Run nginx_test_config, then nginx_apply to load changes.")
    return "\n".join(lines)


def nginx_apply(config: AppConfig, server_name: str | None, *, confirm: bool) -> str:
    if not confirm:
        raise ValueError("nginx_apply requires confirm=true after nginx_test_config passes.")

    server = _server(config, server_name)
    test = run_command(server, "nginx -t")
    if test.exit_code != 0:
        raise RuntimeError(
            "Refusing to reload: nginx -t failed.\n\n" + test.format()
        )

    reload = run_command(server, "systemctl reload nginx")
    lines = [
        f"Server: {server.name} ({server.host})",
        "nginx -t: OK",
        "",
        test.format(),
        "",
        "--- reload ---",
        reload.format(),
    ]
    if reload.exit_code != 0:
        raise RuntimeError("\n".join(lines))
    return "\n".join(lines) + "\n\nNginx reloaded successfully."


def nginx_status(config: AppConfig, server_name: str | None) -> str:
    server = _server(config, server_name)
    result = run_command(server, "systemctl status nginx --no-pager")
    return f"Server: {server.name} ({server.host})\n\n{result.format()}"
