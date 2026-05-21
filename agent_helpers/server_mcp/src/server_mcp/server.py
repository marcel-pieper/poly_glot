from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server_mcp import certbot_ops, nginx_ops, remote_fs
from server_mcp.config import load_config

mcp = FastMCP(
    "server_mcp",
    instructions=(
        "SSH access to configured remote servers. Use list_servers first; pass server name "
        "to other tools (omit for default).\n"
        "Read: list_directory, read_file (preview/offset/limit for large files).\n"
        "Nginx: nginx_list_sites, nginx_test_config, nginx_write_site (full file content), "
        "nginx_enable_site, nginx_disable_site, nginx_apply (requires confirm=true after nginx -t OK). "
        "Always nginx_test_config before nginx_apply.\n"
        "Certbot: certbot_list, certbot_issue (dry_run or confirm=true), "
        "certbot_renew (dry_run default, confirm=true for live)."
    ),
)

_config = None


def _get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config


# --- Read-only filesystem ---


@mcp.tool()
def list_servers() -> str:
    """List configured server aliases and which one is the default."""
    return remote_fs.list_servers(_get_config())


@mcp.tool()
def list_directory(
    path: str,
    server: str | None = None,
    show_hidden: bool = False,
) -> str:
    """
    List entries in a remote directory.

    Args:
        path: Absolute or relative remote path (e.g. /var/log or ~).
        server: Server alias from config. Uses default_server if omitted.
        show_hidden: Include dotfiles when true.
    """
    return remote_fs.list_directory(_get_config(), server, path, show_hidden)


@mcp.tool()
def read_file(
    path: str,
    server: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    preview: bool = False,
) -> str:
    """
    Read a remote text file, with preview or section support for large files.

    Args:
        path: Remote file path.
        server: Server alias from config. Uses default_server if omitted.
        offset: 1-indexed line number to start reading from.
        limit: Maximum number of lines to return.
        preview: When true, return head/tail preview instead of full content.
            Large files auto-preview when offset/limit are not set.
    """
    return remote_fs.read_file(_get_config(), server, path, offset, limit, preview)


# --- Nginx ---


@mcp.tool()
def nginx_list_sites(server: str | None = None) -> str:
    """List files in nginx sites-available and sites-enabled."""
    return nginx_ops.nginx_list_sites(_get_config(), server)


@mcp.tool()
def nginx_test_config(server: str | None = None) -> str:
    """Run nginx -t and return the result."""
    return nginx_ops.nginx_test_config(_get_config(), server)


@mcp.tool()
def nginx_write_site(
    site_name: str,
    content: str,
    server: str | None = None,
    backup: bool = True,
) -> str:
    """
    Write a full nginx site file to sites-available/{site_name}.

    Args:
        site_name: Lowercase name (e.g. polyglot, perfi). Maps to /etc/nginx/sites-available/{site_name}.
        content: Complete nginx server block file content.
        server: Server alias from config.
        backup: If true and the file exists, copy to {site_name}.bak.TIMESTAMP before overwrite.
    """
    return nginx_ops.nginx_write_site(_get_config(), server, site_name, content, backup=backup)


@mcp.tool()
def nginx_enable_site(site_name: str, server: str | None = None) -> str:
    """Enable a site by symlinking sites-available/{site_name} into sites-enabled/."""
    return nginx_ops.nginx_enable_site(_get_config(), server, site_name)


@mcp.tool()
def nginx_disable_site(site_name: str, server: str | None = None) -> str:
    """Disable a site by removing its symlink from sites-enabled/."""
    return nginx_ops.nginx_disable_site(_get_config(), server, site_name)


@mcp.tool()
def nginx_apply(server: str | None = None, confirm: bool = False) -> str:
    """
    Run nginx -t then systemctl reload nginx.

    Args:
        confirm: Must be true. Only call after nginx_test_config succeeds.
    """
    return nginx_ops.nginx_apply(_get_config(), server, confirm=confirm)


@mcp.tool()
def nginx_status(server: str | None = None) -> str:
    """Show systemctl status for nginx."""
    return nginx_ops.nginx_status(_get_config(), server)


# --- Certbot ---


@mcp.tool()
def certbot_list(server: str | None = None) -> str:
    """List certificates managed by certbot."""
    return certbot_ops.certbot_list(_get_config(), server)


@mcp.tool()
def certbot_issue(
    domain: str,
    server: str | None = None,
    dry_run: bool = False,
    confirm: bool = False,
) -> str:
    """
    Issue a certificate with certbot certonly --nginx.

    Args:
        domain: Hostname (e.g. poly.thedevmind.com).
        dry_run: If true, run certbot --dry-run only.
        confirm: If true (and dry_run false), issue a real certificate.
    """
    return certbot_ops.certbot_issue(
        _get_config(), server, domain, dry_run=dry_run, confirm=confirm
    )


@mcp.tool()
def certbot_renew(
    server: str | None = None,
    dry_run: bool = True,
    confirm: bool = False,
) -> str:
    """
    Renew certificates (certbot renew).

    Args:
        dry_run: If true (default), run certbot renew --dry-run.
        confirm: If true and dry_run false, perform a live renewal.
    """
    return certbot_ops.certbot_renew(_get_config(), server, dry_run=dry_run, confirm=confirm)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
