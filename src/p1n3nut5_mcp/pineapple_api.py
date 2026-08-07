"""
REST client for the Hak5 Pineapple Mark VII WebUI backend.

Phase 1: pineapple_status() end-to-end plus the primitives every
higher-level tool composes over (bearer-token auth, structured error
surface, envelope-returning get/post). Everything above that lands in
later phases against `records/pineapple_endpoints.json`.

httpx is a hard dependency (see pyproject.toml). Verification is off by
default because the Pineapple ships a self-signed cert on 172.16.42.1;
callers pass `verify=True` when running against a device with a real
cert.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from p1n3nut5_mcp.runtime import Config


class PineappleAPI:
    def __init__(
        self,
        config: Config,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        config.require_api()
        self._config = config
        self._client = client or httpx.AsyncClient(
            base_url=f"https://{config.host}",
            headers={"Authorization": f"Bearer {config.token}"},
            verify=False,  # self-signed on 172.16.42.1
            timeout=10.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(self, path: str) -> tuple[Any, list[str]]:
        warnings: list[str] = []
        r = await self._client.get(path)
        if r.status_code == 401:
            raise PermissionError(
                f"API auth rejected on {path} — check PINEAPPLE_TOKEN"
            )
        if r.status_code >= 400:
            warnings.append(f"HTTP {r.status_code} on {path}")
        return r.json(), warnings

    async def post(self, path: str, json: Any) -> tuple[Any, list[str]]:
        warnings: list[str] = []
        r = await self._client.post(path, json=json)
        if r.status_code == 401:
            raise PermissionError(
                f"API auth rejected on {path} — check PINEAPPLE_TOKEN"
            )
        if r.status_code >= 400:
            warnings.append(f"HTTP {r.status_code} on {path}")
        return r.json(), warnings

    async def status(self) -> dict:
        """Firmware version, uptime, radios, hostname.

        Composed from the WebUI's own dashboard endpoints. Phase 2 records
        will pin these paths per firmware; for Phase 1 we hit the stable
        v3.x shape.
        """
        payload, warnings = await self.get("/api/dashboard/status")
        return {"payload": payload, "warnings": warnings}

    # --- recon --------------------------------------------------------------

    async def recon_start(self, band: str, dwell_ms: int) -> dict:
        payload, warnings = await self.post(
            "/api/recon/start", {"band": band, "dwell_ms": dwell_ms}
        )
        return {"payload": payload, "warnings": warnings}

    async def recon_stop(self) -> dict:
        payload, warnings = await self.post("/api/recon/stop", {})
        return {"payload": payload, "warnings": warnings}

    async def recon_status(self) -> dict:
        payload, warnings = await self.get("/api/recon/status")
        return {"payload": payload, "warnings": warnings}

    async def list_aps_raw(self) -> dict:
        payload, warnings = await self.get("/api/recon/ap")
        return {"payload": payload, "warnings": warnings}

    async def list_clients_raw(self) -> dict:
        payload, warnings = await self.get("/api/recon/client")
        return {"payload": payload, "warnings": warnings}

    async def list_probe_requests_raw(self) -> dict:
        payload, warnings = await self.get("/api/recon/probes")
        return {"payload": payload, "warnings": warnings}

    async def list_associations_raw(self) -> dict:
        payload, warnings = await self.get("/api/pineap/associations")
        return {"payload": payload, "warnings": warnings}

    # --- PineAP -------------------------------------------------------------

    async def pineap_status(self) -> dict:
        payload, warnings = await self.get("/api/pineap/status")
        return {"payload": payload, "warnings": warnings}

    async def pineap_start(self) -> dict:
        payload, warnings = await self.post("/api/pineap/start", {})
        return {"payload": payload, "warnings": warnings}

    async def pineap_stop(self) -> dict:
        payload, warnings = await self.post("/api/pineap/stop", {})
        return {"payload": payload, "warnings": warnings}

    async def pineap_config(self, config: dict) -> dict:
        payload, warnings = await self.post("/api/pineap/config", config)
        return {"payload": payload, "warnings": warnings}

    async def filter_list(self, kind: str) -> dict:
        payload, warnings = await self.get(f"/api/filter/{kind}")
        return {"payload": payload, "warnings": warnings}

    async def filter_set(self, kind: str, mode: str, items: list[str]) -> dict:
        payload, warnings = await self.post(
            f"/api/filter/{kind}", {"mode": mode, "items": items}
        )
        return {"payload": payload, "warnings": warnings}


async def status(config: Config, client: httpx.AsyncClient | None = None) -> dict:
    """Envelope-returning `pineapple_status()` — API transport."""
    from p1n3nut5_mcp.runtime import envelope

    started = time.monotonic()
    api = PineappleAPI(config, client=client)
    try:
        r = await api.status()
        return envelope(
            ok=True,
            transport="api",
            payload=r["payload"],
            started_at=started,
            warnings=r["warnings"],
        )
    finally:
        if client is None:
            await api.aclose()
