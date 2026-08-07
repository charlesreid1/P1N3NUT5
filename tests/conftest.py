"""
Shared pytest fixtures. Real radio and real Pineapple never appear in CI —
every transport is mocked at the httpx / asyncssh boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
import pytest

from p1n3nut5_mcp.runtime import Config


@pytest.fixture
def api_config() -> Config:
    """Env sufficient to construct an API client."""
    return Config.from_env(
        {
            "PINEAPPLE_HOST": "172.16.42.1",
            "PINEAPPLE_TOKEN": "fake-bearer-token",
        }
    )


@pytest.fixture
def ssh_config() -> Config:
    """Env sufficient to construct an SSH client (password branch)."""
    return Config.from_env(
        {
            "PINEAPPLE_HOST": "172.16.42.1",
            "PINEAPPLE_SSH_PASSWORD": "hak5pineapple",
        }
    )


def make_httpx_client(routes: dict[str, Any]) -> httpx.AsyncClient:
    """Return an httpx.AsyncClient wired to a fake transport.

    `routes` maps request path → response dict (200) or (status, dict).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        entry = routes.get(request.url.path)
        if entry is None:
            return httpx.Response(404, json={"error": "not-found"})
        if isinstance(entry, tuple):
            status, body = entry
        else:
            status, body = 200, entry
        return httpx.Response(status, content=json.dumps(body).encode())

    return httpx.AsyncClient(
        base_url="https://172.16.42.1",
        transport=httpx.MockTransport(handler),
    )


# ---- fake SSH ---------------------------------------------------------------


@dataclass
class FakeProcResult:
    stdout: str
    stderr: str = ""
    exit_status: int | None = 0


class FakeSSHConn:
    def __init__(self, replies: dict[str, FakeProcResult]) -> None:
        self._replies = replies
        self.calls: list[str] = []
        self.closed = False

    async def run(self, command: str, check: bool = False) -> FakeProcResult:
        self.calls.append(command)
        return self._replies.get(
            command,
            FakeProcResult(stdout="", stderr=f"unknown command {command}", exit_status=1),
        )

    async def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:  # asyncssh parity
        pass


def make_ssh_connect(replies: dict[str, FakeProcResult]):
    async def _connect(config: Config) -> FakeSSHConn:
        return FakeSSHConn(replies)

    return _connect
