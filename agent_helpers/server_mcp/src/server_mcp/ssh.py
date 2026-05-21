from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import paramiko

from server_mcp.config import ServerConfig

_clients: dict[str, paramiko.SSHClient] = {}


def _load_pkey(server: ServerConfig) -> paramiko.PKey | None:
    if server.key_file is None:
        return None
    path = server.key_file.expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"SSH key not found for server '{server.name}': {path}")
    passphrase = server.key_passphrase
    for key_cls in (paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.RSAKey):
        try:
            return key_cls.from_private_key_file(str(path), password=passphrase)
        except paramiko.SSHException:
            continue
    raise ValueError(f"Could not load SSH key for server '{server.name}': {path}")


def get_ssh_client(server: ServerConfig) -> paramiko.SSHClient:
    """Return a connected SSH client for the given server."""
    return _connect(server)


def _connect(server: ServerConfig) -> paramiko.SSHClient:
    cached = _clients.get(server.name)
    if cached is not None:
        transport = cached.get_transport()
        if transport is not None and transport.is_active():
            return cached
        cached.close()
        _clients.pop(server.name, None)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs: dict = {
        "hostname": server.host,
        "port": server.port,
        "username": server.user,
        "timeout": server.connect_timeout_seconds,
        "allow_agent": server.key_file is None,
        "look_for_keys": server.key_file is None,
    }
    if server.key_file is not None:
        connect_kwargs["pkey"] = _load_pkey(server)
    client.connect(**connect_kwargs)
    _clients[server.name] = client
    return client


@contextmanager
def sftp_session(server: ServerConfig) -> Iterator[paramiko.SFTPClient]:
    client = _connect(server)
    sftp = client.open_sftp()
    try:
        yield sftp
    finally:
        sftp.close()
