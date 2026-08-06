"""End-to-end tests for recon + PineAP + filter tools (all API)."""

from __future__ import annotations

import json
from pathlib import Path

from p1n3nut5_mcp import server
from p1n3nut5_mcp.pineapple_api import PineappleAPI
from p1n3nut5_mcp.runtime import Config
from tests.conftest import make_httpx_client

FIXTURES = Path(__file__).parent / "fixtures"


def _api_with_routes(api_config: Config, routes: dict) -> PineappleAPI:
    return PineappleAPI(api_config, client=make_httpx_client(routes))


async def test_list_aps_normalizes_and_filters(api_config: Config):
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = _api_with_routes(api_config, {"/api/recon/ap": raw})
    try:
        result = await server.list_aps(api=api, band="2.4", security="wep")
        assert result["ok"] is True
        assert result["transport"] == "api"
        assert len(result["payload"]) == 1
        assert result["payload"][0]["ssid"] == "printer-net"
    finally:
        await api.aclose()


async def test_recon_start_posts_band_and_dwell(api_config: Config):
    captured: dict = {}

    async def _fake_post(path: str, json: dict):
        captured["path"] = path
        captured["json"] = json
        return {"started": True}, []

    api = _api_with_routes(api_config, {"/api/recon/start": {"started": True}})
    try:
        result = await server.recon_start(band="5", dwell_ms=500, api=api)
        assert result["ok"] is True
        assert result["payload"] == {"started": True}
    finally:
        await api.aclose()


async def test_pineap_config_round_trips(api_config: Config):
    api = _api_with_routes(
        api_config, {"/api/pineap/config": {"applied": True}}
    )
    try:
        result = await server.pineap_config(
            {"karma": True, "ssid_pool": ["Starbucks WiFi", "attwifi"]},
            api=api,
        )
        assert result["ok"] is True
        assert result["payload"]["applied"] is True
    finally:
        await api.aclose()


async def test_filter_ssid_set(api_config: Config):
    api = _api_with_routes(api_config, {"/api/filter/ssid": {"mode": "deny", "count": 2}})
    try:
        result = await server.filter_ssid_set("deny", ["target-ap", "sneaky-ap"], api=api)
        assert result["ok"] is True
        assert result["payload"]["mode"] == "deny"
    finally:
        await api.aclose()


async def test_list_probe_requests_normalizes(api_config: Config):
    probes_raw = [
        {"mac": "DE:AD:BE:EF:00:01", "ssid": "home-wifi", "seen_at": 100, "rssi": -40},
        {"mac": "de:ad:be:ef:00:01", "ssid": "cafe", "seen_at": 105, "rssi": -50},
    ]
    api = _api_with_routes(api_config, {"/api/recon/probes": probes_raw})
    try:
        result = await server.list_probe_requests(api=api)
        assert len(result["payload"]) == 2
        assert all(p["client_mac"].islower() for p in result["payload"])
        assert result["payload"][0]["ssid"] == "home-wifi"
    finally:
        await api.aclose()
