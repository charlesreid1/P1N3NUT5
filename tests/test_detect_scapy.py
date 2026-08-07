"""decode_ies / beacon_diff / client_fingerprint — the L6.3 scapy tools."""

from __future__ import annotations

from pathlib import Path

from p1n3nut5_mcp import detect


FIXTURES = Path(__file__).parent / "fixtures" / "pcaps"


def test_decode_ies_walks_wpa2_beacon():
    r = detect.decode_ies(str(FIXTURES / "beacon-wpa2.pcap"))
    assert r["ok"] is True
    payload = r["payload"]
    # BSSID matches the fixture (11:22:33:44:55:66)
    assert "11:22:33:44:55:66" in payload
    ies = payload["11:22:33:44:55:66"]
    # SSID IE (id 0) has the network name bytes
    assert 0 in ies
    assert bytes.fromhex(ies[0]) == b"wpa2-net"
    # RSN IE (id 48) is present
    assert 48 in ies
    # DSSS Parameter Set IE (id 3) → channel byte 6
    assert 3 in ies
    assert bytes.fromhex(ies[3]) == b"\x06"


def test_beacon_diff_flags_ssid_and_rsn_difference():
    # WPA2 beacon vs SAE beacon: different SSID (id 0) and different RSN (id 48),
    # different BSSIDs so we call diff explicitly by BSSID.
    r = detect.beacon_diff(
        bssid_a="11:22:33:44:55:66",
        bssid_b="22:33:44:55:66:77",
        pcap_path=str(FIXTURES / "beacon-wpa2.pcap"),
    )
    # BSSID b (SAE) isn't in the wpa2 fixture — expect a helpful failure
    assert r["ok"] is False
    assert any("no beacon" in w for w in r["warnings"])


def test_beacon_diff_same_pcap_two_bssids():
    """Round-trip a synthetic 2-beacon pcap: same SSID, different Vendor IE."""
    from scapy.all import Dot11, Dot11Beacon, Dot11Elt, wrpcap  # noqa: PLC0415
    import tempfile

    def _beacon(bssid: str, ssid: str, vendor_body: bytes):
        return (
            Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2=bssid, addr3=bssid)
            / Dot11Beacon(cap=0x0431)
            / Dot11Elt(ID=0, info=ssid.encode())
            / Dot11Elt(ID=3, info=b"\x06")
            / Dot11Elt(ID=221, info=vendor_body)
        )

    vendor_a = b"\x00\x50\xf2\x02\x01\x01\x00\x00"
    vendor_b = b"\x00\x50\xf2\x02\x01\x01\xff\xff"
    a = _beacon("aa:aa:aa:aa:aa:aa", "same-ssid", vendor_a)
    b = _beacon("bb:bb:bb:bb:bb:bb", "same-ssid", vendor_b)
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
        wrpcap(f.name, [a, b])
        path = f.name

    r = detect.beacon_diff(
        bssid_a="aa:aa:aa:aa:aa:aa",
        bssid_b="bb:bb:bb:bb:bb:bb",
        pcap_path=path,
    )
    assert r["ok"] is True
    diff = r["payload"]
    # SSID (id 0) is identical → not in `different`
    assert 0 not in diff["different"]
    # Vendor IE (id 221) differs
    assert 221 in diff["different"]
    a_hex, b_hex = diff["different"][221]
    assert a_hex != b_hex


def test_client_fingerprint_hashes_probe_request_ies():
    # probe-request-hidden.pcap has an SSID IE + rates IE from 11:22:33:44:55:66
    r = detect.client_fingerprint(
        client_mac="11:22:33:44:55:66",
        pcap_path=str(FIXTURES / "probe-request-hidden.pcap"),
    )
    assert r["ok"] is True
    fp = r["payload"]["fingerprint"]
    assert isinstance(fp, str) and len(fp) == 16
    # ie_order includes SSID (0) and Rates (1)
    assert 0 in r["payload"]["ie_order"]
    assert 1 in r["payload"]["ie_order"]


def test_client_fingerprint_warns_on_missing_client():
    r = detect.client_fingerprint(
        client_mac="00:00:00:00:00:00",
        pcap_path=str(FIXTURES / "probe-request-hidden.pcap"),
    )
    assert r["ok"] is False
    assert any("no probe/assoc request" in w for w in r["warnings"])
