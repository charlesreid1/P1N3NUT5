"""
run_sequence — the WiFi analog of PHR34CKER5's play_sequence.

One atomic scripted engagement. Given a list of step dicts, execute
them in order against a live Pineapple, honoring the airspace-
authorization envelope for every transmit.

Example from plan-organize.md § "Orchestrate — one atomic scripted
engagement":

    run_sequence([
        {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
        {"action": "wait", "s": 20},
        {"action": "recon_stop"},
        {"action": "capture_handshake", "bssid": "AA:BB:...",
         "timeout_s": 60, "deauth_client": "11:22:..."},
        {"action": "convert_to_hashcat", "mode": 22000},
        {"action": "crack_start", "wordlist_path": "/opt/wordlists/rockyou.txt"},
    ])

Control actions:
  * wait — sleep N seconds
  * wait_until — sleep until an epoch time
  * assert — raise if the previous step's payload does not satisfy a predicate

Each step's result is appended to the returned steps list. If a step
fails and ok=False, the run halts (unless step["continue_on_error"]).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable

from p1n3nut5_mcp.attacks import Authorization
from p1n3nut5_mcp.pineapple_api import PineappleAPI
from p1n3nut5_mcp.pineapple_ssh import PineappleSSH
from p1n3nut5_mcp.runtime import Config


Step = dict[str, Any]
StepResult = dict[str, Any]


class Orchestrator:
    """Long-lived engagement — one API client and one SSH connection."""

    def __init__(
        self,
        config: Config,
        authorization: Authorization,
        *,
        api: PineappleAPI | None = None,
        ssh: PineappleSSH | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.config = config
        self.authorization = authorization
        self._api = api
        self._ssh = ssh
        self._sleep = sleep

    async def _get_api(self) -> PineappleAPI:
        if self._api is None:
            self._api = PineappleAPI(self.config)
        return self._api

    async def _get_ssh(self) -> PineappleSSH:
        if self._ssh is None:
            self._ssh = PineappleSSH(self.config)
        return self._ssh

    async def close(self) -> None:
        if self._api is not None:
            await self._api.aclose()
        if self._ssh is not None:
            await self._ssh.close()

    async def run(self, steps: list[Step]) -> dict:
        from p1n3nut5_mcp import attacks as _attacks  # noqa: PLC0415

        results: list[StepResult] = []
        started = time.monotonic()
        last_ok = True
        for i, step in enumerate(steps):
            action = step.get("action")
            if action is None:
                results.append({"index": i, "ok": False, "error": "missing 'action'"})
                last_ok = False
                if not step.get("continue_on_error"):
                    break
                continue
            result = await self._dispatch(step)
            # MAX_ROGUE_MINUTES enforcement — see docs/legal_and_consent.md.
            # Positive values are a hard cap; 0 means unlimited (skip check).
            if self.config.max_rogue_minutes > 0:
                enforce = await _attacks.enforce_rogue_ap_limits(
                    max_rogue_minutes=self.config.max_rogue_minutes,
                    authorization=self.authorization,
                    ssh=await self._get_ssh(),
                )
                killed = enforce.get("payload", {}).get("killed", [])
                if killed:
                    warnings = list(result.get("warnings") or [])
                    for k in killed:
                        warnings.append(
                            f"rogue AP {k.get('ssid')!r} killed after "
                            f"{k.get('elapsed_minutes')} min "
                            f"(MAX_ROGUE_MINUTES={self.config.max_rogue_minutes}); "
                            f"see docs/legal_and_consent.md"
                        )
                    result = {**result, "warnings": warnings}
            results.append({"index": i, "action": action, **result})
            last_ok = bool(result.get("ok"))
            if not last_ok and not step.get("continue_on_error"):
                break
        return {
            "ok": last_ok,
            "steps": results,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }

    async def _dispatch(self, step: Step) -> StepResult:
        action = step["action"]
        # local imports to avoid a server.py ↔ orchestrate.py import cycle
        from p1n3nut5_mcp import attacks as _attacks
        from p1n3nut5_mcp import detect as _detect
        from p1n3nut5_mcp import hashcat as _hashcat
        from p1n3nut5_mcp import recon as _recon

        if action == "wait":
            await self._sleep(float(step["s"]))
            return {"ok": True, "payload": {"slept_s": step["s"]}}
        if action == "wait_until":
            now = time.time()
            delay = max(0.0, float(step["epoch"]) - now)
            await self._sleep(delay)
            return {"ok": True, "payload": {"slept_s": delay}}

        # --- API-backed ------------------------------------------------------
        api_actions = {
            "recon_start": lambda a: a.recon_start(step.get("band", "both"), step.get("dwell_ms", 250)),
            "recon_stop": lambda a: a.recon_stop(),
            "recon_status": lambda a: a.recon_status(),
            "list_aps_raw": lambda a: a.list_aps_raw(),
            "pineap_start": lambda a: a.pineap_start(),
            "pineap_stop": lambda a: a.pineap_stop(),
            "pineap_config": lambda a: a.pineap_config(step["config"]),
        }
        if action in api_actions:
            api = await self._get_api()
            r = await api_actions[action](api)
            return {"ok": True, "payload": r["payload"], "warnings": r["warnings"]}

        if action == "list_aps":
            api = await self._get_api()
            raw = await api.list_aps_raw()
            aps = [_recon.normalize_ap(x) for x in raw["payload"]]
            filtered = _recon.filter_aps(
                aps,
                seen_since_s=step.get("seen_since_s"),
                ssid_regex=step.get("ssid_regex"),
                band=step.get("band"),
                security=step.get("security"),
            )
            return {"ok": True, "payload": filtered, "warnings": raw["warnings"]}

        # --- SSH-backed ------------------------------------------------------
        if action == "deauth":
            ssh = await self._get_ssh()
            return await _attacks.deauth(
                bssid=step["bssid"],
                client_mac=step.get("client_mac"),
                count=step.get("count", 5),
                reason=step.get("reason", 7),
                iface=step.get("iface", "wlan1mon"),
                respect_pmf=step.get("respect_pmf", True),
                target_pmf=step.get("target_pmf"),
                authorization=self.authorization,
                ssh=ssh,
            )
        if action == "capture_handshake":
            ssh = await self._get_ssh()
            return await _attacks.capture_handshake(
                bssid=step["bssid"],
                timeout_s=step.get("timeout_s", 60),
                out_path=step.get("out_path"),
                deauth_client=step.get("deauth_client"),
                iface=step.get("iface", "wlan1mon"),
                channel=step.get("channel"),
                authorization=self.authorization,
                ssh=ssh,
            )
        if action == "capture_pmkid":
            ssh = await self._get_ssh()
            return await _attacks.capture_pmkid(
                bssid=step.get("bssid"),
                timeout_s=step.get("timeout_s", 60),
                out_path=step.get("out_path"),
                iface=step.get("iface", "wlan1"),
                authorization=self.authorization,
                ssh=ssh,
            )

        # --- Perceive --------------------------------------------------------
        if action == "convert_to_hashcat":
            r = await _detect.convert_to_hashcat(step["pcap_path"], step["out_path"])
            return {
                "ok": r["ok"],
                "payload": [
                    {
                        "type": h.type,
                        "hash_hex": h.hash_hex,
                        "mac_ap": h.mac_ap,
                        "mac_client": h.mac_client,
                        "essid": h.essid,
                        "line": h.line,
                    }
                    for h in r["hash_lines"]
                ],
                "warnings": r["warnings"],
            }
        if action == "crack_start":
            job = await _hashcat.crack_start(
                step["hash_path"],
                step["wordlist_path"],
                mode=step.get("mode", 22000),
                config=self.config,
            )
            return {"ok": True, "payload": {"job_id": job.id, "mode": job.mode}}
        if action == "crack_status":
            return {"ok": True, "payload": _hashcat.crack_status(step["job_id"])}
        if action == "crack_result":
            return {"ok": True, "payload": _hashcat.crack_result(step["job_id"])}

        return {"ok": False, "error": f"unknown action {action!r}"}


async def run_sequence(
    steps: list[Step],
    *,
    i_own_the_airspace: bool = False,
    config: Config | None = None,
    api: PineappleAPI | None = None,
    ssh: PineappleSSH | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> dict:
    cfg = config or Config.from_env()
    orch = Orchestrator(
        cfg,
        Authorization(i_own_the_airspace=i_own_the_airspace),
        api=api,
        ssh=ssh,
        sleep=sleep,
    )
    try:
        return await orch.run(steps)
    finally:
        # Only close resources we created ourselves.
        if api is None and orch._api is not None:
            await orch._api.aclose()
        if ssh is None and orch._ssh is not None:
            await orch._ssh.close()


# --- call_log ---------------------------------------------------------------


def call_log(
    ssh: PineappleSSH | None = None,
    api: PineappleAPI | None = None,
) -> list[dict]:
    """Merged SSH + API call log, ordered by wall-clock start time.

    Each entry is a JSON-safe dict tagged with `transport`. SSH entries
    carry the full command + exit status; API entries carry method +
    path + status. Ordering is by `started_at` (monotonic timestamp
    from the caller's perspective) so a post-engagement audit reads as
    one timeline.
    """
    entries: list[dict] = []
    if ssh is not None:
        for r in ssh.call_log:
            entries.append(
                {
                    "transport": "ssh",
                    "cmd": r.cmd,
                    "stdout": r.stdout,
                    "stderr": r.stderr,
                    "exit_status": r.exit_status,
                    "started_at": r.started_at,
                    "timing_ms": r.timing_ms,
                }
            )
    if api is not None:
        for entry in api.call_log:
            entries.append({"transport": "api", **entry})
    # Sort by started_at if present; entries without it (SSH) keep their
    # append order via a stable sort on a nullable key.
    entries.sort(key=lambda e: e.get("started_at", float("inf")))
    return entries
