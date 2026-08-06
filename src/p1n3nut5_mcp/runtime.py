"""
Config, credential resolution, and session state.

Lazy — nothing here runs at import time, so the offline knowledge tools
still work when `PINEAPPLE_HOST` is not set. See the env-var table in
plan-organize.md for the source of truth on each name.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Literal


class MissingConfig(RuntimeError):
    """Raised when a Pineapple tool is invoked without the env it needs."""


Transport = Literal["api", "ssh"]


@dataclass(frozen=True)
class Config:
    host: str
    token: str | None
    ssh_user: str
    ssh_key: str | None
    ssh_password: str | None
    ssh_port: int
    transport_pref: Transport | None
    max_rogue_minutes: int
    knowledge_root: str | None
    hashcat_path: str | None
    wordlist_dir: str | None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Config":
        e = env if env is not None else dict(os.environ)
        host = e.get("PINEAPPLE_HOST")
        if not host:
            raise MissingConfig(
                "missing env var PINEAPPLE_HOST. See README > Env vars."
            )
        pref_raw = e.get("PINEAPPLE_TRANSPORT_PREF")
        pref: Transport | None
        if pref_raw in (None, ""):
            pref = None
        elif pref_raw in ("api", "ssh"):
            pref = pref_raw  # type: ignore[assignment]
        else:
            raise MissingConfig(
                f"PINEAPPLE_TRANSPORT_PREF must be 'api' or 'ssh', got {pref_raw!r}"
            )
        return cls(
            host=host,
            token=e.get("PINEAPPLE_TOKEN"),
            ssh_user=e.get("PINEAPPLE_SSH_USER", "root"),
            ssh_key=e.get("PINEAPPLE_SSH_KEY"),
            ssh_password=e.get("PINEAPPLE_SSH_PASSWORD"),
            ssh_port=int(e.get("PINEAPPLE_SSH_PORT", "22")),
            transport_pref=pref,
            max_rogue_minutes=int(e.get("MAX_ROGUE_MINUTES", "0")),
            knowledge_root=e.get("P1N3NUT5_KNOWLEDGE"),
            hashcat_path=e.get("HASHCAT_PATH"),
            wordlist_dir=e.get("WORDLIST_DIR"),
        )

    def require_api(self) -> None:
        if not self.token:
            raise MissingConfig(
                "API transport needs PINEAPPLE_TOKEN. See README > Env vars."
            )

    def require_ssh(self) -> None:
        if not self.ssh_key and not self.ssh_password:
            raise MissingConfig(
                "SSH transport needs PINEAPPLE_SSH_KEY or PINEAPPLE_SSH_PASSWORD."
            )


@dataclass
class CallRecord:
    transport: Transport
    target: str
    started_at: float
    duration_ms: int
    ok: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class Session:
    """Per-session state: call log + auth flags."""

    id: str
    calls: list[CallRecord] = field(default_factory=list)
    airspace_authorized: bool = False

    def record(self, r: CallRecord) -> None:
        self.calls.append(r)


def envelope(
    ok: bool,
    transport: Transport,
    payload: object,
    started_at: float,
    warnings: list[str] | None = None,
) -> dict:
    """The stable {ok, transport, payload, timing_ms, warnings[]} shape.

    All Pineapple-touching tools return this. `started_at` is a
    time.monotonic() reading captured before the call.
    """
    return {
        "ok": ok,
        "transport": transport,
        "payload": payload,
        "timing_ms": int((time.monotonic() - started_at) * 1000),
        "warnings": list(warnings or []),
    }
