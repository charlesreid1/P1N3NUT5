"""pineapple_status() end-to-end on both transports — the Phase 1 gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest  # noqa: F401  # imported for monkeypatch fixture typing

from p1n3nut5_mcp import server
from p1n3nut5_mcp.pineapple_api import PineappleAPI, status as api_status
from p1n3nut5_mcp.pineapple_ssh import status as ssh_status
from p1n3nut5_mcp.runtime import Config
from tests.conftest import FakeProcResult, make_httpx_client, make_ssh_connect

FIXTURES = Path(__file__).parent / "fixtures"


# --- API path ---------------------------------------------------------------


async def test_api_status_returns_envelope(api_config: Config):
    dashboard = json.loads((FIXTURES / "api" / "dashboard_status.json").read_text())
    client = make_httpx_client({"/api/dashboard/status": dashboard})
    result = await api_status(api_config, client=client)
    assert result["ok"] is True
    assert result["transport"] == "api"
    assert result["payload"]["firmware"] == "3.1.0"
    assert result["timing_ms"] >= 0
    assert result["warnings"] == []


async def test_api_get_records_http_error_as_warning(api_config: Config):
    client = make_httpx_client({"/api/dashboard/status": (503, {"error": "busy"})})
    api = PineappleAPI(api_config, client=client)
    payload, warnings = await api.get("/api/dashboard/status")
    assert payload == {"error": "busy"}
    assert any("HTTP 503" in w for w in warnings)


async def test_api_401_raises_permission_error(api_config: Config):
    client = make_httpx_client({"/api/dashboard/status": (401, {"error": "nope"})})
    api = PineappleAPI(api_config, client=client)
    with pytest.raises(PermissionError):
        await api.get("/api/dashboard/status")


# --- SSH path ---------------------------------------------------------------


def _ssh_replies() -> dict[str, FakeProcResult]:
    release = (FIXTURES / "ssh" / "openwrt_release.txt").read_text()
    iw = (FIXTURES / "ssh" / "iw_dev.txt").read_text()
    return {
        "cat /etc/openwrt_release 2>/dev/null": FakeProcResult(stdout=release),
        "cat /proc/uptime": FakeProcResult(stdout="4213.42 3893.17\n"),
        "iw dev 2>/dev/null": FakeProcResult(stdout=iw),
    }


async def test_ssh_status_returns_envelope(ssh_config: Config):
    connect = make_ssh_connect(_ssh_replies())
    result = await ssh_status(ssh_config, connect=connect)
    assert result["ok"] is True
    assert result["transport"] == "ssh"
    assert result["payload"]["firmware"] == "21.02.3"
    assert result["payload"]["uptime_s"] == pytest.approx(4213.42)
    ifaces = [r["iface"] for r in result["payload"]["radios"]]
    assert "wlan1mon" in ifaces
    assert "wlan0" in ifaces


async def test_ssh_records_nonzero_exit_as_warning(ssh_config: Config):
    connect = make_ssh_connect(
        {
            "cat /etc/openwrt_release 2>/dev/null": FakeProcResult(stdout=""),
            "cat /proc/uptime": FakeProcResult(stdout="1 1\n"),
            "iw dev 2>/dev/null": FakeProcResult(stdout="", exit_status=1),
        }
    )
    result = await ssh_status(ssh_config, connect=connect)
    assert any("iw dev" in w for w in result["warnings"])


# --- transport-dispatch smoke ------------------------------------------------


async def test_server_pineapple_status_dispatches_by_transport(
    api_config: Config, ssh_config: Config, monkeypatch: pytest.MonkeyPatch
):
    dashboard = json.loads((FIXTURES / "api" / "dashboard_status.json").read_text())

    async def fake_api_status(cfg, client=None):
        return {"ok": True, "transport": "api", "payload": dashboard, "timing_ms": 1, "warnings": []}

    async def fake_ssh_status(cfg, connect=None):
        return {"ok": True, "transport": "ssh", "payload": {"firmware": "21"}, "timing_ms": 1, "warnings": []}

    monkeypatch.setattr(server.pineapple_api, "status", fake_api_status)
    monkeypatch.setattr(server.pineapple_ssh, "status", fake_ssh_status)

    api_result = await server.pineapple_status(transport="api", config=api_config)
    assert api_result["transport"] == "api"

    ssh_result = await server.pineapple_status(transport="ssh", config=ssh_config)
    assert ssh_result["transport"] == "ssh"
