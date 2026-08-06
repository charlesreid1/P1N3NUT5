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

from p1n3nut5_mcp import pineapple_api, pineapple_ssh, pineapple_transport, recon
from p1n3nut5_mcp.runtime import Config, envelope

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


async def _api_call(
    cap: str,
    coro_factory,
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    """Run an API coroutine, wrap in the standard envelope.

    Callers pass `api=` when they want to reuse a client (tests, or a
    long-lived session). Otherwise one is built from `config` and torn
    down at the end.
    """
    import time as _time  # noqa: PLC0415

    cfg = config or (Config.from_env() if api is None else None)
    if cfg is not None:
        pineapple_transport.choose(cap, cfg, request="api")  # validates support
    started = _time.monotonic()
    owned = api is None
    client = api or pineapple_api.PineappleAPI(cfg)  # type: ignore[arg-type]
    try:
        r = await coro_factory(client)
        return envelope(
            ok=True,
            transport="api",
            payload=r["payload"],
            started_at=started,
            warnings=r["warnings"],
        )
    finally:
        if owned:
            await client.aclose()


# --- recon ------------------------------------------------------------------


async def recon_start(
    band: str = "both",
    dwell_ms: int = 250,
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    return await _api_call("recon_start", lambda a: a.recon_start(band, dwell_ms), config, api)


async def recon_stop(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    return await _api_call("recon_stop", lambda a: a.recon_stop(), config, api)


async def recon_status(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    return await _api_call("recon_status", lambda a: a.recon_status(), config, api)


async def list_aps(
    seen_since_s: float | None = None,
    ssid_regex: str | None = None,
    band: str | None = None,
    security: str | None = None,
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    async def _factory(a: pineapple_api.PineappleAPI) -> dict:
        raw = await a.list_aps_raw()
        aps = [recon.normalize_ap(x) for x in raw["payload"]]
        filtered = recon.filter_aps(
            aps,
            seen_since_s=seen_since_s,
            ssid_regex=ssid_regex,
            band=band,
            security=security,
        )
        return {"payload": filtered, "warnings": raw["warnings"]}

    return await _api_call("list_aps", _factory, config, api)


async def list_clients(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    async def _factory(a: pineapple_api.PineappleAPI) -> dict:
        raw = await a.list_clients_raw()
        return {
            "payload": [recon.normalize_client(x) for x in raw["payload"]],
            "warnings": raw["warnings"],
        }

    return await _api_call("list_clients", _factory, config, api)


async def list_probe_requests(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    async def _factory(a: pineapple_api.PineappleAPI) -> dict:
        raw = await a.list_probe_requests_raw()
        return {
            "payload": [recon.normalize_probe(x) for x in raw["payload"]],
            "warnings": raw["warnings"],
        }

    return await _api_call("list_probe_requests", _factory, config, api)


# --- PineAP -----------------------------------------------------------------


async def pineap_status(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    return await _api_call("pineap_status", lambda a: a.pineap_status(), config, api)


async def pineap_start(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    return await _api_call("pineap_start", lambda a: a.pineap_start(), config, api)


async def pineap_stop(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    return await _api_call("pineap_stop", lambda a: a.pineap_stop(), config, api)


async def pineap_config(
    cfg: dict,
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    return await _api_call("pineap_config", lambda a: a.pineap_config(cfg), config, api)


# --- filters ----------------------------------------------------------------


async def filter_ssid_list(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    return await _api_call("filter_ssid_list", lambda a: a.filter_list("ssid"), config, api)


async def filter_ssid_set(
    mode: str,
    ssids: list[str],
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    return await _api_call(
        "filter_ssid_list", lambda a: a.filter_set("ssid", mode, ssids), config, api
    )


async def filter_client_list(
    config: Config | None = None, api: pineapple_api.PineappleAPI | None = None
) -> dict:
    return await _api_call("filter_client_list", lambda a: a.filter_list("client"), config, api)


async def filter_client_set(
    mode: str,
    macs: list[str],
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    return await _api_call(
        "filter_client_list", lambda a: a.filter_set("client", mode, macs), config, api
    )


def main() -> None:
    """FastMCP entry point.

    Import mcp lazily so the test suite can import server.py without
    the mcp package on-path (relevant for CI where only the transport
    layer is exercised).
    """
    from mcp.server.fastmcp import FastMCP  # noqa: PLC0415

    app = FastMCP("p1n3nut5")
    for tool in (
        pineapple_status,
        recon_start,
        recon_stop,
        recon_status,
        list_aps,
        list_clients,
        list_probe_requests,
        pineap_status,
        pineap_start,
        pineap_stop,
        pineap_config,
        filter_ssid_list,
        filter_ssid_set,
        filter_client_list,
        filter_client_set,
    ):
        app.tool()(tool)
    app.run()
