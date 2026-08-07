"""
SSH executor against the Pineapple Mark VII OpenWRT userland.

Phase 1: `run(cmd)` plus a `status()` composed from `cat
/etc/openwrt_release`, `uptime`, and `iw dev` — enough to prove the
plumbing on the SSH surface.

asyncssh is the transport of record. Injected connection factory keeps
the module testable without a live device.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol

from p1n3nut5_mcp.runtime import Config


class _ProcessResult(Protocol):
    stdout: str
    stderr: str
    exit_status: int | None


class _Conn(Protocol):
    async def run(self, command: str, check: bool = ...) -> _ProcessResult: ...
    async def close(self) -> None: ...
    async def wait_closed(self) -> None: ...


ConnectFn = Callable[[Config], Awaitable[_Conn]]


async def _asyncssh_connect(config: Config) -> _Conn:
    """Default connector — lazy-import asyncssh so tests can bypass it."""
    import asyncssh  # noqa: PLC0415

    kwargs: dict[str, Any] = {
        "host": config.host,
        "port": config.ssh_port,
        "username": config.ssh_user,
        "known_hosts": None,  # first-run against a fresh Pineapple
    }
    if config.ssh_key:
        kwargs["client_keys"] = [config.ssh_key]
    elif config.ssh_password:
        kwargs["password"] = config.ssh_password
    return await asyncssh.connect(**kwargs)  # type: ignore[no-any-return]


@dataclass
class RunResult:
    cmd: str
    stdout: str
    stderr: str
    exit_status: int


class PineappleSSH:
    def __init__(
        self,
        config: Config,
        connect: ConnectFn = _asyncssh_connect,
    ) -> None:
        config.require_ssh()
        self._config = config
        self._connect = connect
        self._conn: _Conn | None = None
        self._call_log: list[RunResult] = []

    @property
    def call_log(self) -> list[RunResult]:
        return list(self._call_log)

    async def _ensure(self) -> _Conn:
        if self._conn is None:
            self._conn = await self._connect(self._config)
        return self._conn

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            await self._conn.wait_closed()
            self._conn = None

    async def run(self, cmd: str) -> RunResult:
        conn = await self._ensure()
        r = await conn.run(cmd, check=False)
        result = RunResult(
            cmd=cmd,
            stdout=r.stdout or "",
            stderr=r.stderr or "",
            exit_status=r.exit_status if r.exit_status is not None else -1,
        )
        self._call_log.append(result)
        return result

    async def status(self) -> dict:
        """Firmware version + uptime + radios via shell commands."""
        release = await self.run("cat /etc/openwrt_release 2>/dev/null")
        uptime = await self.run("cat /proc/uptime")
        radios = await self.run("iw dev 2>/dev/null")

        firmware = _extract_openwrt_field(release.stdout, "DISTRIB_RELEASE")
        uptime_s: float | None = None
        try:
            uptime_s = float(uptime.stdout.split()[0])
        except (IndexError, ValueError):
            pass

        payload = {
            "firmware": firmware,
            "uptime_s": uptime_s,
            "radios": _parse_iw_dev(radios.stdout),
        }
        warnings: list[str] = []
        for r in (release, uptime, radios):
            if r.exit_status != 0:
                warnings.append(f"nonzero exit {r.exit_status} for `{r.cmd}`")
        return {"payload": payload, "warnings": warnings}


def _extract_openwrt_field(text: str, key: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip("'\"")
    return None


def _parse_iw_dev(text: str) -> list[dict]:
    radios: list[dict] = []
    current: dict | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Interface "):
            if current is not None:
                radios.append(current)
            current = {"iface": line.split(" ", 1)[1]}
        elif current is not None and " " in line:
            k, _, v = line.partition(" ")
            k = k.strip().rstrip(":")
            if k in ("addr", "type", "channel", "ssid"):
                current[k] = v.strip()
    if current is not None:
        radios.append(current)
    return radios


async def list_interfaces(
    config: Config, connect: ConnectFn = _asyncssh_connect
) -> dict:
    """Envelope-returning `list_interfaces()` — SSH transport."""
    from p1n3nut5_mcp.runtime import envelope

    started = time.monotonic()
    ssh = PineappleSSH(config, connect=connect)
    try:
        r = await ssh.run("iw dev 2>/dev/null")
        warnings: list[str] = []
        if r.exit_status != 0:
            warnings.append(f"iw dev exit {r.exit_status}")
        return envelope(
            ok=r.exit_status == 0,
            transport="ssh",
            payload=_parse_iw_dev(r.stdout),
            started_at=started,
            warnings=warnings,
        )
    finally:
        await ssh.close()


async def status(config: Config, connect: ConnectFn = _asyncssh_connect) -> dict:
    """Envelope-returning `pineapple_status()` — SSH transport."""
    from p1n3nut5_mcp.runtime import envelope

    started = time.monotonic()
    ssh = PineappleSSH(config, connect=connect)
    try:
        r = await ssh.status()
        return envelope(
            ok=True,
            transport="ssh",
            payload=r["payload"],
            started_at=started,
            warnings=r["warnings"],
        )
    finally:
        await ssh.close()
