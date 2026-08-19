"""End-to-end tests for recon + PineAP + filter tools (all API)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from p1n3nut5_mcp import server
from p1n3nut5_mcp.pineapple_api import PineappleAPI
from p1n3nut5_mcp.runtime import Config
from tests.conftest import make_httpx_client

FIXTURES = Path(__file__).parent / "fixtures"


def _api_with_routes(api_config: Config, routes: dict) -> PineappleAPI:
    return PineappleAPI(api_config, client=make_httpx_client(routes))


@pytest.fixture
def stub_api_client(monkeypatch):
    """Monkeypatch `server._api_client` to return a shared PineappleAPI.

    `_api_call` closes the client it gets back from the factory. The
    test also closes the same client in its own `finally`, so we wrap
    the returned client with a no-op `aclose` and rely on the test's
    `finally` to close the real underlying transport.
    """

    def _install(api: PineappleAPI) -> None:
        class _Shim:
            def __init__(self, inner: PineappleAPI) -> None:
                self._inner = inner

            def __getattr__(self, name: str):
                return getattr(self._inner, name)

            async def aclose(self) -> None:  # noqa: D401 — swallow double-close
                pass

        monkeypatch.setattr(server, "_api_client", lambda cfg: _Shim(api))

    return _install


async def test_list_aps_normalizes_and_filters(api_config: Config, stub_api_client):
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = _api_with_routes(api_config, {"/api/recon/ap": raw})
    stub_api_client(api)
    try:
        result = await server.list_aps(band="2.4", security="wep", config=api_config)
        assert result["ok"] is True
        assert result["transport"] == "api"
        assert len(result["payload"]) == 1
        assert result["payload"][0]["ssid"] == "printer-net"
    finally:
        await api.aclose()


async def test_recon_start_posts_band_and_dwell(api_config: Config, stub_api_client):
    api = _api_with_routes(api_config, {"/api/recon/start": {"started": True}})
    stub_api_client(api)
    try:
        result = await server.recon_start(band="5", dwell_ms=500, config=api_config)
        assert result["ok"] is True
        assert result["payload"] == {"started": True}
    finally:
        await api.aclose()


async def test_pineap_config_round_trips(api_config: Config, stub_api_client):
    api = _api_with_routes(
        api_config, {"/api/pineap/config": {"applied": True}}
    )
    stub_api_client(api)
    try:
        result = await server.pineap_config(
            {"karma": True, "ssid_pool": ["Starbucks WiFi", "attwifi"]},
            config=api_config,
        )
        assert result["ok"] is True
        assert result["payload"]["applied"] is True
    finally:
        await api.aclose()


async def test_filter_ssid_set(api_config: Config, stub_api_client):
    api = _api_with_routes(api_config, {"/api/filter/ssid": {"mode": "deny", "count": 2}})
    stub_api_client(api)
    try:
        result = await server.filter_ssid_set(
            "deny", ["target-ap", "sneaky-ap"], config=api_config
        )
        assert result["ok"] is True
        assert result["payload"]["mode"] == "deny"
    finally:
        await api.aclose()


async def test_pineap_beacon_add_posts_ssids(api_config: Config, stub_api_client):
    api = _api_with_routes(api_config, {"/api/pineap/ssid/add": {"added": 2}})
    stub_api_client(api)
    try:
        r = await server.pineap_beacon_add(
            ["Starbucks WiFi", "attwifi"], config=api_config
        )
        assert r["ok"] is True
        assert r["payload"] == {"added": 2}
    finally:
        await api.aclose()


async def test_pineap_beacon_remove_posts_ssids(api_config: Config, stub_api_client):
    api = _api_with_routes(api_config, {"/api/pineap/ssid/remove": {"removed": 1}})
    stub_api_client(api)
    try:
        r = await server.pineap_beacon_remove(["stale-ssid"], config=api_config)
        assert r["ok"] is True
        assert r["payload"] == {"removed": 1}
    finally:
        await api.aclose()


async def test_get_ap_details_filters_list_aps(api_config: Config, stub_api_client):
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = _api_with_routes(api_config, {"/api/recon/ap": raw})
    stub_api_client(api)
    try:
        target = raw[0]["bssid"].lower()
        r = await server.get_ap_details(bssid=target, config=api_config)
        assert r["ok"] is True
        assert r["payload"]["bssid"] == target
    finally:
        await api.aclose()


async def test_get_ap_details_warns_when_missing(api_config: Config, stub_api_client):
    raw = json.loads((FIXTURES / "api" / "recon_ap.json").read_text())
    api = _api_with_routes(api_config, {"/api/recon/ap": raw})
    stub_api_client(api)
    try:
        r = await server.get_ap_details(
            bssid="00:00:00:00:00:00", config=api_config
        )
        assert r["ok"] is True
        assert r["payload"] is None
        assert any("not in current recon set" in w for w in r["warnings"])
    finally:
        await api.aclose()


async def test_list_associations_pulls_from_pineap_endpoint(
    api_config: Config, stub_api_client
):
    payload = [
        {"mac": "aa:bb:cc:dd:ee:ff", "bssid": "00:c0:ca:12:34:56", "since": 100},
        {"mac": "11:22:33:44:55:66", "bssid": "00:c0:ca:12:34:56", "since": 200},
    ]
    api = _api_with_routes(api_config, {"/api/pineap/associations": payload})
    stub_api_client(api)
    try:
        result = await server.list_associations(config=api_config)
        assert result["ok"] is True
        assert result["transport"] == "api"
        assert result["payload"] == payload
    finally:
        await api.aclose()


async def test_list_probe_requests_normalizes(api_config: Config, stub_api_client):
    probes_raw = [
        {"mac": "DE:AD:BE:EF:00:01", "ssid": "home-wifi", "seen_at": 100, "rssi": -40},
        {"mac": "de:ad:be:ef:00:01", "ssid": "cafe", "seen_at": 105, "rssi": -50},
    ]
    api = _api_with_routes(api_config, {"/api/recon/probes": probes_raw})
    stub_api_client(api)
    try:
        result = await server.list_probe_requests(config=api_config)
        assert len(result["payload"]) == 2
        assert all(p["client_mac"].islower() for p in result["payload"])
        assert result["payload"][0]["ssid"] == "home-wifi"
    finally:
        await api.aclose()
