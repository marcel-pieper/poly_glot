from __future__ import annotations

from dataclasses import dataclass

from server_mcp.config import ServerConfig
from server_mcp.ssh import get_ssh_client

MAX_OUTPUT_CHARS = 64_000
DEFAULT_COMMAND_TIMEOUT = 120


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str

    def format(self) -> str:
        lines = [
            f"Command: {self.command}",
            f"Exit code: {self.exit_code}",
        ]
        if self.stdout.strip():
            lines.extend(["", "--- stdout ---", self.stdout.rstrip()])
        if self.stderr.strip():
            lines.extend(["", "--- stderr ---", self.stderr.rstrip()])
        return "\n".join(lines)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... (truncated, {len(text)} chars total)"


def run_command(
    server: ServerConfig,
    command: str,
    *,
    timeout: int = DEFAULT_COMMAND_TIMEOUT,
) -> CommandResult:
    client = get_ssh_client(server)
    _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = _truncate(stdout.read().decode("utf-8", errors="replace"))
    err = _truncate(stderr.read().decode("utf-8", errors="replace"))
    return CommandResult(command=command, exit_code=exit_code, stdout=out, stderr=err)


def run_checked(server: ServerConfig, command: str, *, timeout: int = DEFAULT_COMMAND_TIMEOUT) -> str:
    result = run_command(server, command, timeout=timeout)
    if result.exit_code != 0:
        raise RuntimeError(result.format())
    return result.format()
