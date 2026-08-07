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

from p1n3nut5_mcp import (
    attacks,
    detect,
    hashcat as hashcat_mod,
    knowledge as kb,
    orchestrate,
    pineapple_api,
    pineapple_ssh,
    pineapple_transport,
    recon,
)
from p1n3nut5_mcp.attacks import Authorization
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


async def pineap_beacon_add(
    ssids: list[str],
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    return await _api_call(
        "pineap_beacon_add", lambda a: a.pineap_beacon_add(ssids), config, api
    )


async def pineap_beacon_remove(
    ssids: list[str],
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    return await _api_call(
        "pineap_beacon_remove", lambda a: a.pineap_beacon_remove(ssids), config, api
    )


async def get_ap_details(
    bssid: str,
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    """Return the single AP entry (from list_aps) keyed by BSSID.

    Zero new endpoints — reuses `list_aps_raw` + `normalize_ap` and
    filters to the target BSSID. If unseen, returns payload=null with
    a warning; the caller can retry after another recon pass.
    """
    async def _factory(a: pineapple_api.PineappleAPI) -> dict:
        raw = await a.list_aps_raw()
        want = bssid.lower()
        for x in raw["payload"]:
            ap = recon.normalize_ap(x)
            if ap["bssid"] == want:
                return {"payload": ap, "warnings": raw["warnings"]}
        return {
            "payload": None,
            "warnings": list(raw["warnings"])
            + [f"bssid {bssid!r} not in current recon set — run recon_start first"],
        }

    return await _api_call("get_ap_details", _factory, config, api)


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


# --- Act — attack primitives (SSH-heavy) -----------------------------------


async def _with_ssh(coro_factory, config: Config | None = None) -> dict:
    cfg = config or Config.from_env()
    ssh = pineapple_ssh.PineappleSSH(cfg)
    try:
        return await coro_factory(ssh)
    finally:
        await ssh.close()


async def do_deauth(
    bssid: str,
    client_mac: str | None = None,
    count: int = 5,
    reason: int = 7,
    iface: str = "wlan1mon",
    respect_pmf: bool = True,
    i_own_the_airspace: bool = False,
    target_pmf: str | None = None,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    if ssh is not None:
        return await attacks.deauth(
            bssid=bssid, client_mac=client_mac, count=count, reason=reason,
            iface=iface, respect_pmf=respect_pmf, authorization=authz,
            ssh=ssh, target_pmf=target_pmf,
        )
    return await _with_ssh(
        lambda s: attacks.deauth(
            bssid=bssid, client_mac=client_mac, count=count, reason=reason,
            iface=iface, respect_pmf=respect_pmf, authorization=authz,
            ssh=s, target_pmf=target_pmf,
        ),
        config,
    )


async def do_capture_handshake(
    bssid: str,
    timeout_s: int = 60,
    out_path: str | None = None,
    deauth_client: str | None = None,
    iface: str = "wlan1mon",
    channel: int | None = None,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    kw = dict(bssid=bssid, timeout_s=timeout_s, out_path=out_path,
              deauth_client=deauth_client, iface=iface, channel=channel,
              authorization=authz)
    if ssh is not None:
        return await attacks.capture_handshake(**kw, ssh=ssh)
    return await _with_ssh(lambda s: attacks.capture_handshake(**kw, ssh=s), config)


async def do_capture_pmkid(
    bssid: str | None = None,
    timeout_s: int = 60,
    out_path: str | None = None,
    iface: str = "wlan1",
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    kw = dict(bssid=bssid, timeout_s=timeout_s, out_path=out_path, iface=iface,
              authorization=authz)
    if ssh is not None:
        return await attacks.capture_pmkid(**kw, ssh=ssh)
    return await _with_ssh(lambda s: attacks.capture_pmkid(**kw, ssh=s), config)


async def do_create_rogue_ap(
    ssid: str,
    channel: int,
    security: str = "open",
    psk: str | None = None,
    bssid: str | None = None,
    iface: str = "wlan0",
    band: str = "2.4",
    hidden: bool = False,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    kw = dict(ssid=ssid, channel=channel, security=security, psk=psk, bssid=bssid,
              iface=iface, band=band, hidden=hidden, authorization=authz)
    if ssh is not None:
        return await attacks.create_rogue_ap(**kw, ssh=ssh)
    return await _with_ssh(lambda s: attacks.create_rogue_ap(**kw, ssh=s), config)


async def do_stop_rogue_ap(
    handle: str,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    if ssh is not None:
        return await attacks.stop_rogue_ap(handle=handle, authorization=authz, ssh=ssh)
    return await _with_ssh(
        lambda s: attacks.stop_rogue_ap(handle=handle, authorization=authz, ssh=s),
        config,
    )


async def do_stop_all_rogue_aps(
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    if ssh is not None:
        return await attacks.stop_all_rogue_aps(ssh=ssh, authorization=authz)
    return await _with_ssh(
        lambda s: attacks.stop_all_rogue_aps(ssh=s, authorization=authz),
        config,
    )


async def do_beacon_flood(
    iface: str,
    ssid_file: str,
    channel: int | None = None,
    duration_s: int = 60,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    kw = dict(iface=iface, ssid_file=ssid_file, channel=channel,
              duration_s=duration_s, authorization=authz)
    if ssh is not None:
        return await attacks.beacon_flood(**kw, ssh=ssh)
    return await _with_ssh(lambda s: attacks.beacon_flood(**kw, ssh=s), config)


async def do_packet_inject(
    pcap_path: str,
    iface: str,
    count: int = 1,
    interval_ms: int = 100,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    kw = dict(pcap_path=pcap_path, iface=iface, count=count,
              interval_ms=interval_ms, authorization=authz)
    if ssh is not None:
        return await attacks.packet_inject(**kw, ssh=ssh)
    return await _with_ssh(lambda s: attacks.packet_inject(**kw, ssh=s), config)


async def do_channel_hop_start(
    iface: str,
    channels: list[int],
    dwell_ms: int = 250,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    kw = dict(iface=iface, channels=list(channels), dwell_ms=dwell_ms,
              authorization=authz)
    if ssh is not None:
        return await attacks.channel_hop_start(**kw, ssh=ssh)
    return await _with_ssh(lambda s: attacks.channel_hop_start(**kw, ssh=s), config)


async def do_channel_hop_stop(
    handle: str,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    if ssh is not None:
        return await attacks.channel_hop_stop(handle=handle, authorization=authz, ssh=ssh)
    return await _with_ssh(
        lambda s: attacks.channel_hop_stop(handle=handle, authorization=authz, ssh=s),
        config,
    )


async def do_list_interfaces(
    config: Config | None = None,
) -> dict:
    cfg = config or Config.from_env()
    return await pineapple_ssh.list_interfaces(cfg)


def do_list_rogue_aps() -> dict:
    """Snapshot of the rogue-AP registry — every AP this MCP launched.

    Not authorization-gated: pure read of module state, no wire traffic.
    """
    return {"ok": True, "payload": attacks.list_rogue_aps()}


async def enforce_rogue_limits(
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    """Manually run MAX_ROGUE_MINUTES enforcement; returns killed handles.

    The orchestrator fires this automatically between steps whenever
    `config.max_rogue_minutes > 0`. Operators can also hit this
    directly to see what would be killed right now.
    """
    cfg = config or Config.from_env()
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    if ssh is not None:
        return await attacks.enforce_rogue_ap_limits(
            max_rogue_minutes=cfg.max_rogue_minutes,
            authorization=authz,
            ssh=ssh,
        )
    return await _with_ssh(
        lambda s: attacks.enforce_rogue_ap_limits(
            max_rogue_minutes=cfg.max_rogue_minutes,
            authorization=authz,
            ssh=s,
        ),
        cfg,
    )


async def list_associations(
    config: Config | None = None,
    api: pineapple_api.PineappleAPI | None = None,
) -> dict:
    return await _api_call(
        "list_associations", lambda a: a.list_associations_raw(), config, api
    )


async def do_evil_twin(
    target_bssid: str,
    target_ssid: str,
    target_channel: int,
    deauth_clients: bool = True,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    ssh: pineapple_ssh.PineappleSSH | None = None,
) -> dict:
    authz = Authorization(i_own_the_airspace=i_own_the_airspace)
    kw = dict(target_bssid=target_bssid, target_ssid=target_ssid,
              target_channel=target_channel, deauth_clients=deauth_clients,
              authorization=authz)
    if ssh is not None:
        return await attacks.evil_twin(**kw, ssh=ssh)
    return await _with_ssh(lambda s: attacks.evil_twin(**kw, ssh=s), config)


# --- Perceive (local, no radio) ---------------------------------------------


def parse_pcap(path: str) -> dict:
    summary = detect.parse_pcap(path)
    return {
        "ok": True,
        "payload": {
            "total_frames": summary.total_frames,
            "frame_type_counts": summary.frame_type_counts,
            "bssids": summary.bssids,
            "ssids": summary.ssids,
            "clients": summary.clients,
        },
    }


def _hashline_dicts(lines) -> list[dict]:
    return [
        {
            "type": h.type,
            "hash_hex": h.hash_hex,
            "mac_ap": h.mac_ap,
            "mac_client": h.mac_client,
            "essid": h.essid,
            "line": h.line,
        }
        for h in lines
    ]


async def convert_to_hashcat(pcap_path: str, out_path: str) -> dict:
    r = await detect.convert_to_hashcat(pcap_path, out_path)
    return {"ok": r["ok"], "payload": _hashline_dicts(r["hash_lines"]), "warnings": r["warnings"]}


async def extract_handshakes(pcap_path: str, out_path: str) -> dict:
    r = await detect.extract_handshakes(pcap_path, out_path)
    return {"ok": r["ok"], "payload": _hashline_dicts(r["hash_lines"]), "warnings": r["warnings"]}


async def extract_pmkids(pcap_path: str, out_path: str) -> dict:
    r = await detect.extract_pmkids(pcap_path, out_path)
    return {"ok": r["ok"], "payload": _hashline_dicts(r["hash_lines"]), "warnings": r["warnings"]}


async def crack_start(
    hash_path: str,
    wordlist_path: str,
    mode: int = 22000,
    config: Config | None = None,
) -> dict:
    job = await hashcat_mod.crack_start(hash_path, wordlist_path, mode=mode, config=config)
    return {"ok": True, "payload": {"job_id": job.id, "mode": job.mode}}


def crack_status(job_id: str) -> dict:
    return hashcat_mod.crack_status(job_id)


def crack_result(job_id: str) -> dict:
    return hashcat_mod.crack_result(job_id)


async def crack_stop(job_id: str) -> dict:
    return await hashcat_mod.crack_stop(job_id)


# --- Orchestrate ------------------------------------------------------------


async def run_sequence(
    steps: list[dict],
    i_own_the_airspace: bool = False,
    config: Config | None = None,
) -> dict:
    """Atomic scripted engagement — the run_sequence tool.

    See plan-organize.md § 'Orchestrate — one atomic scripted engagement'
    for the action vocabulary.
    """
    return await orchestrate.run_sequence(
        steps, i_own_the_airspace=i_own_the_airspace, config=config
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
        pineap_beacon_add,
        pineap_beacon_remove,
        get_ap_details,
        filter_ssid_list,
        filter_ssid_set,
        filter_client_list,
        filter_client_set,
        parse_pcap,
        convert_to_hashcat,
        extract_handshakes,
        extract_pmkids,
        crack_start,
        crack_status,
        crack_result,
        crack_stop,
        do_deauth,
        do_capture_handshake,
        do_capture_pmkid,
        do_create_rogue_ap,
        do_stop_rogue_ap,
        do_stop_all_rogue_aps,
        do_beacon_flood,
        do_packet_inject,
        do_channel_hop_start,
        do_channel_hop_stop,
        do_list_interfaces,
        do_list_rogue_aps,
        enforce_rogue_limits,
        list_associations,
        do_evil_twin,
        run_sequence,
        # Know — typed records (Phase-2 KR tools; see plan-knowledge.md)
        kb.lookup_standard,
        kb.lookup_channel,
        kb.lookup_frame,
        kb.lookup_ie,
        kb.lookup_cipher,
        kb.lookup_eap,
        kb.lookup_attack,
        kb.lookup_cve,
        kb.lookup_hashcat_mode,
        kb.bibliography,
        kb.cross_reference,
        kb.search_records,
        kb.verify_claim,
        kb.explain_attack,
        # Know — prose corpus
        kb.list_topics,
        kb.read_lore,
        kb.search_lore,
        kb.random_lore,
    ):
        app.tool()(tool)
    app.run()
