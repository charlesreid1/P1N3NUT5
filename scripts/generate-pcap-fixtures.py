#!/usr/bin/env python3
"""
Deterministic pcap generator for tests/fixtures/pcaps/.

Emits small, hand-crafted classic-pcap files with known frame contents
so the perception tools (parse_pcap, extract_*) have a stable target
that does not require a live capture.

Files produced:
  - beacon-open.pcap             one 802.11 beacon frame, open network
  - beacon-wpa2.pcap             one 802.11 beacon frame, WPA2 RSN IE
  - beacon-wpa3-sae.pcap         WPA3-SAE beacon (RSN AKM 8, PMF-required)
  - beacon-wpa3-transition.pcap  WPA2 + WPA3 SAE transition beacon
  - deauth-reason-7.pcap         a deauth with reason=7 (WCTF flag surface)
  - probe-request-hidden.pcap    client probing a hidden SSID (SSID reveal)
  - probe-response-karma.pcap    AP karma-responds to a probe request
  - handshake-hcx.txt            fixture 22000 hash line (WPA*02 + WPA*01)

Every fixture is keyed by a Tier-1 attack record id in the corpus:
  beacon-wpa2.pcap        -> attacks.json:wpa2-4way-capture
  beacon-wpa3-sae.pcap    -> attacks.json:wpa3-transition-downgrade (contrast)
  beacon-wpa3-transition  -> attacks.json:wpa3-transition-downgrade
  deauth-reason-7.pcap    -> attacks.json:deauth-broadcast / deauth-targeted
  probe-request-hidden    -> ctf/hidden-ssid-mazes
  probe-response-karma    -> attacks.json:mana-karma / pineap-active-karma
  handshake-hcx.txt       -> attacks.json:pmkid-capture + wpa2-4way-capture

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


def write_wpa3_sae_beacon() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # RSN IE: PMF-required (MFPR=1, MFPC=1 => 0xc0 in RSN Cap byte 0),
    # group=CCMP, pairwise=CCMP, AKM=SAE (00-0f-ac-08),
    # RSN Cap = 0x00c0, no PMKID, group mgmt = BIP-CMAC (00-0f-ac-06).
    rsn_body = (
        b"\x01\x00"
        + b"\x00\x0f\xac\x04"                          # group cipher
        + b"\x01\x00" + b"\x00\x0f\xac\x04"            # pairwise
        + b"\x01\x00" + b"\x00\x0f\xac\x08"            # AKM SAE
        + b"\xc0\x00"                                  # RSN Cap: PMF required
        + b"\x00\x00"                                  # PMKID count = 0
        + b"\x00\x0f\xac\x06"                          # group mgmt = BIP-CMAC-128
    )
    rsn_ie = bytes([48, len(rsn_body)]) + rsn_body
    frame = _beacon(b"\x22\x33\x44\x55\x66\x77", "sae-net", rsn_ie=rsn_ie)
    (OUT / "beacon-wpa3-sae.pcap").write_bytes(_pcap_header() + _pcap_record(frame))


def write_wpa3_transition_beacon() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Transition mode: AKM list contains BOTH PSK (00-0f-ac-02) AND SAE (00-0f-ac-08).
    # A WPA2-capable client will happily fall back to the PSK side — the
    # downgrade opportunity attacks.json:wpa3-transition-downgrade attacks.
    rsn_body = (
        b"\x01\x00"
        + b"\x00\x0f\xac\x04"                          # group cipher CCMP
        + b"\x01\x00" + b"\x00\x0f\xac\x04"            # pairwise CCMP
        + b"\x02\x00"                                  # AKM count = 2
        + b"\x00\x0f\xac\x02"                          # AKM 1: PSK
        + b"\x00\x0f\xac\x08"                          # AKM 2: SAE
        + b"\x80\x00"                                  # RSN Cap: PMF capable, not required
    )
    rsn_ie = bytes([48, len(rsn_body)]) + rsn_body
    frame = _beacon(b"\x33\x44\x55\x66\x77\x88", "transit-net", rsn_ie=rsn_ie)
    (OUT / "beacon-wpa3-transition.pcap").write_bytes(_pcap_header() + _pcap_record(frame))


def write_deauth_reason_7() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # 802.11 deauth: fc=0xc000 (type 0 subtype 12), addr1 (dest), addr2 (src=AP),
    # addr3 (BSSID), seq, then 2-byte reason code = 7 (little-endian).
    fc = struct.pack("<H", 0x00c0)
    dur = b"\x00\x00"
    dst = b"\x11\x22\x33\x44\x55\x66"     # target client
    src = b"\xaa\xbb\xcc\xdd\xee\xff"     # AP BSSID (spoofed source)
    bssid = src
    seq = b"\x00\x00"
    reason = struct.pack("<H", 7)         # class 3 frame from nonassociated STA
    frame = fc + dur + dst + src + bssid + seq + reason
    (OUT / "deauth-reason-7.pcap").write_bytes(_pcap_header() + _pcap_record(frame))


def write_probe_request_hidden() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Probe Request from a client naming a hidden SSID — the reveal
    # mechanic. fc=0x0040 (type 0 subtype 4).
    fc = struct.pack("<H", 0x0040)
    dur = b"\x00\x00"
    addr1 = b"\xff\xff\xff\xff\xff\xff"   # broadcast
    addr2 = b"\x11\x22\x33\x44\x55\x66"   # client MAC
    addr3 = b"\xff\xff\xff\xff\xff\xff"
    seq = b"\x00\x00"
    hdr = fc + dur + addr1 + addr2 + addr3 + seq
    # SSID IE naming the previously-hidden network + supported rates
    ssid_str = "hidden-corp"
    ssid_ie = bytes([0, len(ssid_str)]) + ssid_str.encode()
    rates_ie = bytes([1, 4, 0x82, 0x84, 0x8b, 0x96])
    frame = hdr + ssid_ie + rates_ie
    (OUT / "probe-request-hidden.pcap").write_bytes(_pcap_header() + _pcap_record(frame))


def write_probe_response_karma() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Probe Response — karma-style, AP answers to any SSID the client
    # asked about. fc=0x0050 (type 0 subtype 5).
    fc = struct.pack("<H", 0x0050)
    dur = b"\x00\x00"
    addr1 = b"\x11\x22\x33\x44\x55\x66"   # unicast to the probing client
    addr2 = b"\xaa\xbb\xcc\xdd\xee\xff"   # rogue AP BSSID
    addr3 = addr2
    seq = b"\x00\x00"
    hdr = fc + dur + addr1 + addr2 + addr3 + seq
    fixed = b"\x00" * 8 + struct.pack("<H", 100) + struct.pack("<H", 0x0421)
    ssid_str = "AttendeeHomeNet"       # the SSID the client probed for
    ssid_ie = bytes([0, len(ssid_str)]) + ssid_str.encode()
    ds_ie = bytes([3, 1, 6])
    frame = hdr + fixed + ssid_ie + ds_ie
    (OUT / "probe-response-karma.pcap").write_bytes(_pcap_header() + _pcap_record(frame))


def write_pcapng_beacon() -> None:
    """Same open-beacon frame as beacon-open.pcap, wrapped in pcapng.

    Regression fixture for L6 pcapng support — parse_pcap must return a
    non-empty summary from this file even though it uses the pcapng
    magic (0x0a0d0d0a) rather than classic pcap.
    """
    from scapy.utils import PcapNgWriter  # noqa: PLC0415
    from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Elt  # noqa: PLC0415

    OUT.mkdir(parents=True, exist_ok=True)
    pkt = (
        Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff",
              addr2="aa:bb:cc:dd:ee:ff", addr3="aa:bb:cc:dd:ee:ff")
        / Dot11Beacon(cap=0x0431)
        / Dot11Elt(ID=0, info=b"open-net")
        / Dot11Elt(ID=3, info=b"\x06")
    )
    path = OUT / "beacon-open.pcapng"
    with PcapNgWriter(str(path)) as w:
        w.write(pkt)


if __name__ == "__main__":
    write_open_beacon()
    write_wpa2_beacon()
    write_wpa3_sae_beacon()
    write_wpa3_transition_beacon()
    write_deauth_reason_7()
    write_probe_request_hidden()
    write_probe_response_karma()
    write_22000_lines()
    write_pcapng_beacon()
    print(f"wrote fixtures under {OUT}")
