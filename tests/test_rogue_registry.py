"""Rogue-AP registry contract — create/list/stop/enforce.

Phase L4 makes `MAX_ROGUE_MINUTES` actually enforce. This test locks
in the registry contract: `create_rogue_ap` registers on successful
launch, `stop_rogue_ap` deregisters, `enforce_rogue_ap_limits` kills
handles past the threshold, `list_rogue_aps` reflects reality.
"""

from __future__ import annotations

import pytest

from p1n3nut5_mcp import attacks
from p1n3nut5_mcp.attacks import Authorization, _ROGUE_REGISTRY
from p1n3nut5_mcp.pineapple_ssh import PineappleSSH
from p1n3nut5_mcp.runtime import Config
from tests.conftest import FakeProcResult, FakeSSHConn


class RecorderSSH(FakeSSHConn):
    async def run(self, command: str, check: bool = False):
        self.calls.append(command)
        return FakeProcResult(stdout="", exit_status=0)


def _ssh() -> PineappleSSH:
    async def connect(cfg):
        return RecorderSSH({})

    return PineappleSSH(
        Config.from_env({"PINEAPPLE_HOST": "x", "PINEAPPLE_SSH_PASSWORD": "y"}),
        connect=connect,
    )


@pytest.fixture(autouse=True)
def clean_registry():
    _ROGUE_REGISTRY.clear()
    yield
    _ROGUE_REGISTRY.clear()


async def test_create_rogue_ap_registers():
    ssh = _ssh()
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.create_rogue_ap(
        ssid="corp-rogue", channel=6, authorization=authz, ssh=ssh
    )
    assert r["ok"] is True
    entries = attacks.list_rogue_aps()
    assert len(entries) == 1
    assert entries[0]["ssid"] == "corp-rogue"
    assert entries[0]["channel"] == 6
    assert entries[0]["handle"].endswith(".pid")


async def test_stop_rogue_ap_deregisters():
    ssh = _ssh()
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.create_rogue_ap(
        ssid="rogue-a", channel=1, authorization=authz, ssh=ssh
    )
    handle = r["payload"]["handle"]
    await attacks.stop_rogue_ap(handle=handle, authorization=authz, ssh=ssh)
    assert attacks.list_rogue_aps() == []


async def test_stop_all_rogue_aps_drains_registry():
    ssh = _ssh()
    authz = Authorization(i_own_the_airspace=True)
    await attacks.create_rogue_ap(ssid="a", channel=1, authorization=authz, ssh=ssh)
    await attacks.create_rogue_ap(ssid="b", channel=6, authorization=authz, ssh=ssh)
    assert len(attacks.list_rogue_aps()) == 2
    await attacks.stop_all_rogue_aps(ssh=ssh, authorization=authz)
    assert attacks.list_rogue_aps() == []


async def test_enforce_rogue_ap_limits_kills_past_threshold():
    ssh = _ssh()
    authz = Authorization(i_own_the_airspace=True)
    r1 = await attacks.create_rogue_ap(
        ssid="old-rogue", channel=1, authorization=authz, ssh=ssh
    )
    r2 = await attacks.create_rogue_ap(
        ssid="new-rogue", channel=6, authorization=authz, ssh=ssh
    )
    # backdate old-rogue by 10 minutes
    _ROGUE_REGISTRY[r1["payload"]["handle"]]["started_at"] -= 10 * 60

    result = await attacks.enforce_rogue_ap_limits(
        max_rogue_minutes=5, authorization=authz, ssh=ssh
    )
    killed = result["payload"]["killed"]
    assert len(killed) == 1
    assert killed[0]["ssid"] == "old-rogue"
    assert killed[0]["cite"] == "docs/legal_and_consent.md"
    assert killed[0]["elapsed_minutes"] >= 5
    # remaining registry has only new-rogue
    handles = [e["handle"] for e in attacks.list_rogue_aps()]
    assert handles == [r2["payload"]["handle"]]


async def test_enforce_rogue_ap_limits_zero_means_unlimited():
    ssh = _ssh()
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.create_rogue_ap(
        ssid="stays-alive", channel=1, authorization=authz, ssh=ssh
    )
    _ROGUE_REGISTRY[r["payload"]["handle"]]["started_at"] -= 60 * 60 * 24  # 1 day
    result = await attacks.enforce_rogue_ap_limits(
        max_rogue_minutes=0, authorization=authz, ssh=ssh
    )
    assert result["payload"]["killed"] == []
    assert len(attacks.list_rogue_aps()) == 1
