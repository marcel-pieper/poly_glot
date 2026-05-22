from __future__ import annotations

import atexit
from typing import TYPE_CHECKING

import paramiko
from sshtunnel import SSHTunnelForwarder

if TYPE_CHECKING:
    from database_mcp.config import SshConfig

_tunnels: dict[str, SSHTunnelForwarder] = {}


def _load_pkey(ssh: SshConfig) -> paramiko.PKey:
    if ssh.key_file is None:
        raise ValueError("ssh.key_file is required to load a private key")
    path = ssh.key_file
    passphrase = ssh.key_passphrase
    for key_cls in (paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.RSAKey):
        try:
            return key_cls.from_private_key_file(str(path), password=passphrase)
        except paramiko.SSHException:
            continue
    raise ValueError(f"Could not load SSH private key: {path}")


def _is_forwarder_active(forwarder: SSHTunnelForwarder) -> bool:
    if getattr(forwarder, "is_active", None) is not None:
        return bool(forwarder.is_active)
    tunnel = getattr(forwarder, "tunnel_is_up", None)
    if isinstance(tunnel, dict):
        return any(tunnel.values())
    return forwarder.local_bind_port is not None


def get_local_bind_port(database_name: str, ssh: SshConfig) -> int:
    """Start or reuse an SSH tunnel for this database alias; return the local TCP port."""
    existing = _tunnels.get(database_name)
    if existing is not None and _is_forwarder_active(existing):
        port = existing.local_bind_port
        if port is not None:
            return int(port)

    if existing is not None:
        try:
            existing.stop()
        except Exception:
            pass
        _tunnels.pop(database_name, None)

    kwargs: dict = {
        "ssh_address_or_host": (ssh.host, ssh.port),
        "ssh_username": ssh.user,
        "remote_bind_address": (ssh.remote_host, ssh.remote_port),
        "local_bind_address": ("127.0.0.1", ssh.local_port),
        "allow_agent": False,
        "host_pkey_directories": [],
    }
    if ssh.key_file is not None:
        kwargs["ssh_pkey"] = _load_pkey(ssh)
    else:
        kwargs["allow_agent"] = True

    forwarder = SSHTunnelForwarder(**kwargs)
    try:
        forwarder.start()
    except Exception as exc:
        raise ConnectionError(
            f"SSH tunnel to {ssh.user}@{ssh.host}:{ssh.port} "
            f"(remote {ssh.remote_host}:{ssh.remote_port}) failed: {exc}"
        ) from exc

    port = forwarder.local_bind_port
    if port is None:
        forwarder.stop()
        raise ConnectionError(f"SSH tunnel for database '{database_name}' did not bind a local port")

    _tunnels[database_name] = forwarder
    return int(port)


@atexit.register
def _stop_all_tunnels() -> None:
    for name, forwarder in list(_tunnels.items()):
        try:
            forwarder.stop()
        except Exception:
            pass
        _tunnels.pop(name, None)
