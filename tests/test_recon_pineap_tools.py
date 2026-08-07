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


async def test_pineap_beacon_add_posts_ssids(api_config: Config):
    api = _api_with_routes(api_config, {"/api/pineap/ssid/add": {"added": 2}})
    try:
        r = await server.pineap_beacon_add(["Starbucks WiFi", "attwifi"], api=api)
        assert r["ok"] is True
        assert r["payload"] == {"added": 2}
    finally:
        await api.aclose()


async def test_pineap_beacon_remove_posts_ssids(api_config: Config):
    api = _api_with_routes(api_config, {"/api/pineap/ssid/remove": {"removed": 1}})
    try:
        r = await server.pineap_beacon_remove(["stale-ssid"], api=api)
        assert r["ok"] is True
        assert r["payload"] == {"removed": 1}
    finally:
        await api.aclose()


async def test_get_ap_details_filters_list_aps(api_config: Config):
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = _api_with_routes(api_config, {"/api/recon/ap": raw})
    try:
        # Target the first BSSID in the fixture.
        target = raw[0]["bssid"].lower()
        r = await server.get_ap_details(bssid=target, api=api)
        assert r["ok"] is True
        assert r["payload"]["bssid"] == target
    finally:
        await api.aclose()


async def test_get_ap_details_warns_when_missing(api_config: Config):
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = _api_with_routes(api_config, {"/api/recon/ap": raw})
    try:
        r = await server.get_ap_details(bssid="00:00:00:00:00:00", api=api)
        assert r["ok"] is True
        assert r["payload"] is None
        assert any("not in current recon set" in w for w in r["warnings"])
    finally:
        await api.aclose()


async def test_list_associations_pulls_from_pineap_endpoint(api_config: Config):
    payload = [
        {"mac": "aa:bb:cc:dd:ee:ff", "bssid": "00:c0:ca:12:34:56", "since": 100},
        {"mac": "11:22:33:44:55:66", "bssid": "00:c0:ca:12:34:56", "since": 200},
    ]
    api = _api_with_routes(api_config, {"/api/pineap/associations": payload})
    try:
        result = await server.list_associations(api=api)
        assert result["ok"] is True
        assert result["transport"] == "api"
        assert result["payload"] == payload
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
