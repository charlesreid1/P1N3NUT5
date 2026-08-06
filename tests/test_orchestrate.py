"""Phase 7 — run_sequence + call_log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from p1n3nut5_mcp import orchestrate
from p1n3nut5_mcp.attacks import Authorization
from p1n3nut5_mcp.orchestrate import Orchestrator, call_log
from p1n3nut5_mcp.pineapple_api import PineappleAPI
from p1n3nut5_mcp.pineapple_ssh import PineappleSSH
from p1n3nut5_mcp.runtime import Config
from tests.conftest import FakeProcResult, FakeSSHConn, make_httpx_client, make_ssh_connect

FIXTURES = Path(__file__).parent / "fixtures"


def _cfg() -> Config:
    return Config.from_env({"PINEAPPLE_HOST": "x", "PINEAPPLE_SSH_PASSWORD": "y", "PINEAPPLE_TOKEN": "t"})


async def test_wait_action_uses_injected_sleeper():
    slept: list[float] = []

    async def fake_sleep(s: float) -> None:
        slept.append(s)

    orch = Orchestrator(_cfg(), Authorization(i_own_the_airspace=True), sleep=fake_sleep)
    r = await orch.run([{"action": "wait", "s": 0.5}])
    assert r["ok"] is True
    assert slept == [0.5]


async def test_recon_then_list_aps_composes():
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = PineappleAPI(
        _cfg(),
        client=make_httpx_client(
            {"/api/recon/start": {"started": True}, "/api/recon/ap": raw}
        ),
    )

    async def no_sleep(s: float) -> None:
        pass

    orch = Orchestrator(_cfg(), Authorization(i_own_the_airspace=True), api=api, sleep=no_sleep)
    r = await orch.run(
        [
            {"action": "recon_start", "band": "2.4"},
            {"action": "wait", "s": 0.01},
            {"action": "list_aps", "band": "2.4", "security": "wep"},
        ]
    )
    await api.aclose()
    assert r["ok"] is True
    assert r["steps"][-1]["action"] == "list_aps"
    assert [ap["ssid"] for ap in r["steps"][-1]["payload"]] == ["printer-net"]


async def test_capture_handshake_step_carries_authorization():
    class Recorder(FakeSSHConn):
        async def run(self, command: str, check: bool = False):
            self.calls.append(command)
            return FakeProcResult(stdout="", exit_status=124)

    async def connect(cfg):
        return Recorder({})

    ssh = PineappleSSH(_cfg(), connect=connect)

    async def no_sleep(s: float) -> None:
        pass

    orch = Orchestrator(
        _cfg(),
        Authorization(i_own_the_airspace=True),
        ssh=ssh,
        sleep=no_sleep,
    )
    r = await orch.run(
        [
            {
                "action": "capture_handshake",
                "bssid": "aa:bb:cc:dd:ee:ff",
                "timeout_s": 30,
            }
        ]
    )
    assert r["ok"] is True
    cmds = [c.cmd for c in ssh.call_log]
    assert any("airodump-ng" in c and "aa:bb:cc:dd:ee:ff" in c for c in cmds)


async def test_run_halts_on_step_failure_by_default():
    orch = Orchestrator(
        _cfg(),
        Authorization(i_own_the_airspace=True),
        sleep=lambda s: __import__("asyncio").sleep(0),
    )
    r = await orch.run(
        [
            {"action": "no_such_action"},  # ok=False
            {"action": "wait", "s": 0.001},
        ]
    )
    assert r["ok"] is False
    assert len(r["steps"]) == 1  # halted after failure


async def test_continue_on_error_lets_subsequent_steps_run():
    slept: list[float] = []

    async def fake_sleep(s: float) -> None:
        slept.append(s)

    orch = Orchestrator(
        _cfg(),
        Authorization(i_own_the_airspace=True),
        sleep=fake_sleep,
    )
    r = await orch.run(
        [
            {"action": "no_such_action", "continue_on_error": True},
            {"action": "wait", "s": 0.5},
        ]
    )
    assert len(r["steps"]) == 2
    assert slept == [0.5]


async def test_call_log_serializes_ssh_history():
    class Recorder(FakeSSHConn):
        async def run(self, command: str, check: bool = False):
            self.calls.append(command)
            return FakeProcResult(stdout="hi", exit_status=0)

    async def connect(cfg):
        return Recorder({})

    ssh = PineappleSSH(_cfg(), connect=connect)
    await ssh.run("iw dev")
    await ssh.run("uptime")
    log = call_log(ssh)
    assert [entry["cmd"] for entry in log] == ["iw dev", "uptime"]
    assert all(entry["exit_status"] == 0 for entry in log)


async def test_run_sequence_module_entry_point():
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = PineappleAPI(_cfg(), client=make_httpx_client({"/api/recon/ap": raw}))

    async def no_sleep(s: float) -> None:
        pass

    r = await orchestrate.run_sequence(
        [{"action": "list_aps"}],
        i_own_the_airspace=True,
        config=_cfg(),
        api=api,
        sleep=no_sleep,
    )
    await api.aclose()
    assert r["ok"] is True
    assert len(r["steps"][0]["payload"]) == 4
