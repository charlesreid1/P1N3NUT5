"""Config.from_env — the plumbing everything else stands on."""

from __future__ import annotations

import pytest

from p1n3nut5_mcp.runtime import Config, MissingConfig


def test_from_env_requires_host():
    with pytest.raises(MissingConfig, match="PINEAPPLE_HOST"):
        Config.from_env({})


def test_defaults_apply():
    c = Config.from_env({"PINEAPPLE_HOST": "172.16.42.1"})
    assert c.host == "172.16.42.1"
    assert c.ssh_user == "root"
    assert c.ssh_port == 22
    assert c.transport_pref is None
    assert c.token is None


def test_transport_pref_validated():
    with pytest.raises(MissingConfig, match="PINEAPPLE_TRANSPORT_PREF"):
        Config.from_env(
            {"PINEAPPLE_HOST": "172.16.42.1", "PINEAPPLE_TRANSPORT_PREF": "carrier-pigeon"}
        )


def test_transport_pref_accepts_api_and_ssh():
    for pref in ("api", "ssh"):
        c = Config.from_env(
            {"PINEAPPLE_HOST": "172.16.42.1", "PINEAPPLE_TRANSPORT_PREF": pref}
        )
        assert c.transport_pref == pref


def test_require_api_needs_token():
    c = Config.from_env({"PINEAPPLE_HOST": "172.16.42.1"})
    with pytest.raises(MissingConfig, match="PINEAPPLE_TOKEN"):
        c.require_api()


def test_require_ssh_needs_key_or_password():
    c = Config.from_env({"PINEAPPLE_HOST": "172.16.42.1"})
    with pytest.raises(MissingConfig, match="PINEAPPLE_SSH_KEY"):
        c.require_ssh()

    c_key = Config.from_env(
        {"PINEAPPLE_HOST": "172.16.42.1", "PINEAPPLE_SSH_KEY": "/tmp/id_ed25519"}
    )
    c_key.require_ssh()  # does not raise

    c_pw = Config.from_env(
        {"PINEAPPLE_HOST": "172.16.42.1", "PINEAPPLE_SSH_PASSWORD": "x"}
    )
    c_pw.require_ssh()
