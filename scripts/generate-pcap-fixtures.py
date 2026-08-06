#!/usr/bin/env python3
"""
Deterministic pcap generator for tests/fixtures/pcaps/.

Emits small, hand-crafted classic-pcap files with known frame contents
so the perception tools (parse_pcap, extract_*) have a stable target
that does not require a live capture.

Files produced:
  - beacon-open.pcap        one 802.11 beacon frame, open network
  - beacon-wpa2.pcap        one 802.11 beacon frame, WPA2 RSN IE
  - handshake-hcx.txt       fixture 22000 hash line (WPA*02 + WPA*01)

The handshake-hcx.txt file stands in for hcxpcapngtool output — tests
inject a fake `run` callable that writes this file so we don't need
hcxtools installed in CI.
"""

from __future__ import annotations

import struct
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "pcaps"


def _pcap_header() -> bytes:
    # magic, version_major, version_minor, thiszone, sigfigs, snaplen, network
    # network = 105 = LINKTYPE_IEEE802_11 (no radiotap header for these fixtures)
    return struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 105)


def _pcap_record(payload: bytes) -> bytes:
    return struct.pack("<IIII", 0, 0, len(payload), len(payload)) + payload


def _beacon(bssid: bytes, ssid: str, rsn_ie: bytes = b"") -> bytes:
    # 802.11 header: fc=0x8000 beacon, duration=0, addr1=bcast, addr2=bssid,
    # addr3=bssid, seq=0
    fc = struct.pack("<H", 0x0080)  # type=0 (mgmt), subtype=8 (beacon)
    dur = b"\x00\x00"
    addr1 = b"\xff\xff\xff\xff\xff\xff"
    seq = b"\x00\x00"
    hdr = fc + dur + addr1 + bssid + bssid + seq
    # fixed params: timestamp(8) + beacon interval(2) + capability(2)
    fixed = b"\x00" * 8 + struct.pack("<H", 100) + struct.pack("<H", 0x0431)
    # SSID IE + DS parameter IE (channel 6)
    ssid_ie = bytes([0, len(ssid)]) + ssid.encode()
    ds_ie = bytes([3, 1, 6])
    return hdr + fixed + ssid_ie + ds_ie + rsn_ie


def write_open_beacon() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = _beacon(b"\xaa\xbb\xcc\xdd\xee\xff", "open-net")
    (OUT / "beacon-open.pcap").write_bytes(_pcap_header() + _pcap_record(frame))


def write_wpa2_beacon() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # RSN IE: id=48, len=20, version=1,
    # group cipher=00-0F-AC-04 (CCMP-128),
    # pairwise count=1, 00-0F-AC-04,
    # AKM count=1, 00-0F-AC-02 (PSK),
    # RSN capabilities=0x0000
    rsn_body = (
        b"\x01\x00"
        + b"\x00\x0f\xac\x04"
        + b"\x01\x00" + b"\x00\x0f\xac\x04"
        + b"\x01\x00" + b"\x00\x0f\xac\x02"
        + b"\x00\x00"
    )
    rsn_ie = bytes([48, len(rsn_body)]) + rsn_body
    frame = _beacon(b"\x11\x22\x33\x44\x55\x66", "wpa2-net", rsn_ie=rsn_ie)
    (OUT / "beacon-wpa2.pcap").write_bytes(_pcap_header() + _pcap_record(frame))


def write_22000_lines() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    essid_hex = "6d792d61702d31".ljust(64, "0")[: len("6d792d61702d31")]  # "my-ap-1"
    # PMKID (TYPE=01): WPA*01*PMKID*MAC_AP*MAC_CLIENT*ESSID_HEX***
    pmkid_line = (
        "WPA*01*"
        "abababababababababababababababab*"
        "aabbccddeeff*"
        "112233445566*"
        f"{essid_hex}"
        "***"
    )
    # EAPOL (TYPE=02): WPA*02*MIC*MAC_AP*MAC_CLIENT*ESSID_HEX*ANONCE*EAPOL*MP
    eapol_line = (
        "WPA*02*"
        "cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd*"
        "aabbccddeeff*"
        "112233445566*"
        f"{essid_hex}*"
        "de" * 32 + "*"
        "aa" * 121 + "*"
        "00"
    )
    (OUT / "handshake-hcx.txt").write_text(pmkid_line + "\n" + eapol_line + "\n")


if __name__ == "__main__":
    write_open_beacon()
    write_wpa2_beacon()
    write_22000_lines()
    print(f"wrote fixtures under {OUT}")
