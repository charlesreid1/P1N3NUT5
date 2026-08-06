"""The API-vs-SSH decision rule from plan-organize.md."""

from __future__ import annotations

import pytest

from p1n3nut5_mcp.pineapple_transport import (
    CAPABILITY_RULES,
    UnknownCapability,
    choose,
)
from p1n3nut5_mcp.runtime import Config


def _cfg(pref: str | None = None) -> Config:
    env = {"PINEAPPLE_HOST": "x"}
    if pref:
        env["PINEAPPLE_TRANSPORT_PREF"] = pref
    return Config.from_env(env)


def test_default_prefers_api_for_status():
    assert choose("status", _cfg()) == "api"


def test_ssh_only_capability_returns_ssh():
    assert choose("deauth", _cfg()) == "ssh"
    assert choose("capture_handshake", _cfg()) == "ssh"


def test_env_pref_wins_when_capability_supports_it():
    assert choose("status", _cfg("ssh")) == "ssh"
    assert choose("status", _cfg("api")) == "api"


def test_env_pref_ignored_when_capability_does_not_support_it():
    # deauth is SSH-only. PINEAPPLE_TRANSPORT_PREF=api must not switch it.
    assert choose("deauth", _cfg("api")) == "ssh"


def test_explicit_request_overrides_everything():
    assert choose("status", _cfg("api"), request="ssh") == "ssh"


def test_explicit_request_validated_against_capability():
    with pytest.raises(ValueError, match="does not support"):
        choose("deauth", _cfg(), request="api")


def test_unknown_capability_raises():
    with pytest.raises(UnknownCapability):
        choose("teleport", _cfg())


def test_every_rule_declares_supported_transports():
    for cap, (preferred, fallback) in CAPABILITY_RULES.items():
        assert preferred in ("api", "ssh"), cap
        assert fallback in (None, "api", "ssh"), cap
        assert fallback != preferred, cap
