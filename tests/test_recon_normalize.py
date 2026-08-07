"""Recon-DB normalization and filter helpers."""

from __future__ import annotations

import json
from pathlib import Path

from p1n3nut5_mcp import recon


FIXTURES = Path(__file__).parent / "fixtures"


def _raw() -> list[dict]:
    return json.loads((FIXTURES / "api" / "recon_ap.json").read_text())


def test_normalize_nested_security_shape():
    ap = recon.normalize_ap(_raw()[0])
    assert ap["bssid"] == "aa:bb:cc:dd:ee:ff"  # canonical lower-case
    assert ap["ssid"] == "conference-wifi"
    assert ap["channel"] == 6
    assert ap["security"] == "wpa2-psk"  # AKM 2 → wpa2-psk
    assert ap["security_detail"]["pmf"] == "disabled"


def test_normalize_wpa3_akm_8():
    ap = recon.normalize_ap(_raw()[1])
    assert ap["security"] == "wpa3-sae"
    assert ap["security_detail"]["pmf"] == "required"


def test_normalize_flat_security_string():
    ap = recon.normalize_ap(_raw()[2])
    assert ap["security"] == "wep"
    assert ap["security_detail"] is None


def test_filter_by_security():
    aps = [recon.normalize_ap(x) for x in _raw()]
    wep = recon.filter_aps(aps, security="wep")
    assert len(wep) == 1
    assert wep[0]["ssid"] == "printer-net"


def test_filter_by_band():
    aps = [recon.normalize_ap(x) for x in _raw()]
    five = recon.filter_aps(aps, band="5")
    assert [a["channel"] for a in five] == [149]
    twofour = recon.filter_aps(aps, band="2.4")
    assert sorted(a["channel"] for a in twofour) == [1, 6, 11]


def test_filter_by_ssid_regex():
    aps = [recon.normalize_ap(x) for x in _raw()]
    corp = recon.filter_aps(aps, ssid_regex="^corp-")
    assert len(corp) == 1
    assert corp[0]["ssid"] == "corp-wpa3"


def test_filter_by_seen_since():
    aps = [recon.normalize_ap(x) for x in _raw()]
    # now=1000, seen_since_s=10 → drop the printer (last_seen=500)
    recent = recon.filter_aps(aps, seen_since_s=10, now=1000)
    assert all(a["ssid"] != "printer-net" for a in recent)
    assert len(recent) == 3
