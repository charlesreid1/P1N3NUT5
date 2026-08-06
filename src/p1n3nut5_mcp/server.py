"""
P1N3NUT5 MCP server — tool declarations.

Phase 1 wires `pineapple_status()` end-to-end. Every tool that touches
the Pineapple returns the stable envelope
    {ok, transport, payload, timing_ms, warnings[]}
declared in plan-organize.md. Phases 3–7 add the rest of the tool
inventory (recon, PineAP, perceive, attack, orchestrate).
"""

from __future__ import annotations

from typing import Literal

from p1n3nut5_mcp import pineapple_api, pineapple_ssh, pineapple_transport
from p1n3nut5_mcp.runtime import Config

URI_SCHEME = "p1n3nut5"


async def pineapple_status(
    transport: Literal["api", "ssh"] | None = None,
    config: Config | None = None,
) -> dict:
    """Reachable? firmware? uptime? radios present?

    `transport` overrides the per-capability rule. Default respects
    PINEAPPLE_TRANSPORT_PREF, then the rule in CAPABILITY_RULES ('api').
    """
    cfg = config or Config.from_env()
    chosen = pineapple_transport.choose("status", cfg, request=transport)
    if chosen == "api":
        return await pineapple_api.status(cfg)
    return await pineapple_ssh.status(cfg)


def main() -> None:
    """FastMCP entry point.

    Import mcp lazily so the test suite can import server.py without
    the mcp package on-path (relevant for CI where only the transport
    layer is exercised).
    """
    from mcp.server.fastmcp import FastMCP  # noqa: PLC0415

    app = FastMCP("p1n3nut5")
    app.tool()(pineapple_status)
    app.run()
