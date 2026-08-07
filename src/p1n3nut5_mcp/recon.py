"""
Recon-DB normalizers.

The WebUI's recon payloads come in different shapes across firmwares
(3.0 flattened `security`; 3.1 nested `security.{akm,cipher,pmf}`).
The MCP tool contract is stable — the response shape declared in
plan-knowledge.md § "pineapple_endpoints.json — list_aps":

    {bssid, ssid, channel, rssi, security, last_seen, ies?}

Phase 3 does the light normalization. Phase 2 records will pin exact
shapes per firmware — this module then binds to those.
"""

from __future__ import annotations

import re
import time
from typing import Any


def normalize_ap(raw: dict) -> dict:
    """Return a canonical AP record from any WebUI shape we know about."""
    security = raw.get("security")
    if isinstance(security, dict):
        # 3.1+ nested shape — collapse to a short label for the payload,
        # but keep the full dict under `security_detail`.
        akm = security.get("akm") or security.get("key_management")
        detail = security
        label = _label_from_akm(akm) or "unknown"
    else:
        label = (security or "unknown").lower()
        detail = None
    return {
        "bssid": raw["bssid"].lower(),
        "ssid": raw.get("ssid", ""),
        "channel": raw.get("channel"),
        "rssi": raw.get("rssi"),
        "security": label,
        "security_detail": detail,
        "last_seen": raw.get("last_seen") or raw.get("lastSeen"),
        "ies": raw.get("ies"),
    }


def _label_from_akm(akm: Any) -> str | None:
    if isinstance(akm, list) and akm:
        akm = akm[0]
    if isinstance(akm, int):
        return {
            0: "open",
            1: "wpa2-eap",
            2: "wpa2-psk",
            8: "wpa3-sae",
            12: "owe",
            18: "wpa3-sae-ext-key",
        }.get(akm)
    if isinstance(akm, str):
        return akm.lower()
    return None


def filter_aps(
    aps: list[dict],
    *,
    seen_since_s: float | None = None,
    ssid_regex: str | None = None,
    band: str | None = None,
    security: str | None = None,
    now: float | None = None,
) -> list[dict]:
    now = now if now is not None else time.time()
    pattern = re.compile(ssid_regex) if ssid_regex else None
    out = []
    for ap in aps:
        if seen_since_s is not None and ap.get("last_seen") is not None:
            if now - float(ap["last_seen"]) > seen_since_s:
                continue
        if pattern is not None and not pattern.search(ap.get("ssid") or ""):
            continue
        if band is not None and _band_of(ap.get("channel")) != band:
            continue
        if security is not None and ap.get("security") != security:
            continue
        out.append(ap)
    return out


def _band_of(channel: int | None) -> str | None:
    if channel is None:
        return None
    if 1 <= channel <= 14:
        return "2.4"
    if 32 <= channel <= 177:
        return "5"
    # 6 GHz uses channels 1..233 per 802.11ax, but 2.4 GHz already claims
    # 1..14 and 5 GHz claims 32..177 in this numbering; the WebUI signals
    # 6 GHz recon hits with numbers >= 200 (matching channels.json).
    if 200 <= channel <= 233:
        return "6"
    return None


def normalize_client(raw: dict) -> dict:
    return {
        "mac": raw["mac"].lower(),
        "vendor": raw.get("vendor"),
        "associated_bssid": (raw.get("associated_bssid") or raw.get("bssid") or "").lower() or None,
        "last_seen": raw.get("last_seen") or raw.get("lastSeen"),
        "rssi": raw.get("rssi"),
        "probes": raw.get("probes", []),
    }


def normalize_probe(raw: dict) -> dict:
    return {
        "client_mac": raw["mac"].lower(),
        "ssid": raw.get("ssid", ""),
        "seen_at": raw.get("seen_at") or raw.get("lastSeen"),
        "rssi": raw.get("rssi"),
    }
