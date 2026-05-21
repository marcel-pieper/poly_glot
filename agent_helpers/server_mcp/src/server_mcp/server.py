from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server_mcp import remote_fs
from server_mcp.config import load_config

mcp = FastMCP(
    "server_mcp",
    instructions=(
        "Read-only SSH access to configured remote servers. "
        "Use list_servers first, then pass server name to other tools. "
        "Omit server to use the configured default. "
        "For large files, use preview=true or offset/limit (1-indexed lines)."
    ),
)

_config = None


def _get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config


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


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
