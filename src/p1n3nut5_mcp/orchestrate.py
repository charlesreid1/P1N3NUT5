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


def call_log(ssh: PineappleSSH | None = None) -> list[dict]:
    """Return the SSH call_log as JSON-serializable dicts.

    Extended in Phase 7+ to merge API + SSH calls once the API client
    grows its own logger; for now the API layer is stateless per-call.
    """
    if ssh is None:
        return []
    return [
        {"cmd": r.cmd, "stdout": r.stdout, "stderr": r.stderr, "exit_status": r.exit_status}
        for r in ssh.call_log
    ]
