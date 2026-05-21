from __future__ import annotations

from server_mcp.config import AppConfig, ServerConfig
from server_mcp.nginx_guard import validate_domain
from server_mcp.remote_exec import run_command

CERTBOT_TIMEOUT = 300


def _server(config: AppConfig, server_name: str | None) -> ServerConfig:
    return config.get_server(server_name)


def certbot_list(config: AppConfig, server_name: str | None) -> str:
    server = _server(config, server_name)
    result = run_command(server, "certbot certificates", timeout=CERTBOT_TIMEOUT)
    return f"Server: {server.name} ({server.host})\n\n{result.format()}"


def certbot_issue(
    config: AppConfig,
    server_name: str | None,
    domain: str,
    *,
    dry_run: bool = False,
    confirm: bool = False,
) -> str:
    d = validate_domain(domain)
    if dry_run:
        flag = "--dry-run"
    elif confirm:
        flag = ""
    else:
        raise ValueError(
            "certbot_issue requires dry_run=true for a trial, or confirm=true to issue a real certificate."
        )

    server = _server(config, server_name)
    parts = ["certbot", "certonly", "--nginx", "-d", d, "--non-interactive", "--agree-tos"]
    if flag:
        parts.append(flag)
    command = " ".join(parts)
    result = run_command(server, command, timeout=CERTBOT_TIMEOUT)

    header = [
        f"Server: {server.name} ({server.host})",
        f"Domain: {d}",
        f"Mode: {'dry-run' if dry_run else 'live'}",
        "",
        result.format(),
    ]
    if result.exit_code != 0:
        raise RuntimeError("\n".join(header))
    if dry_run:
        header.append("")
        header.append("Dry run succeeded. Re-run with confirm=true to issue the real certificate.")
    else:
        header.append("")
        header.append("Certificate issued. Update nginx SSL paths if needed, then nginx_apply.")
    return "\n".join(header)


def certbot_renew(
    config: AppConfig,
    server_name: str | None,
    *,
    dry_run: bool = True,
    confirm: bool = False,
) -> str:
    if dry_run:
        command = "certbot renew --dry-run"
        mode = "dry-run"
    elif confirm:
        command = "certbot renew"
        mode = "live"
    else:
        raise ValueError(
            "certbot_renew requires dry_run=true (default) for a trial, or confirm=true to renew for real."
        )

    server = _server(config, server_name)
    result = run_command(server, command, timeout=CERTBOT_TIMEOUT)
    header = [
        f"Server: {server.name} ({server.host})",
        f"Mode: {mode}",
        "",
        result.format(),
    ]
    if result.exit_code != 0:
        raise RuntimeError("\n".join(header))
    return "\n".join(header)
