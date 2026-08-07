"""
Pcap parsing and handshake / PMKID extraction.

Local. Runs on the MCP host so an offline pcap analysis works without
the Pineapple attached. Two paths:

  * `hcxpcapngtool` (from hcxtools) — the canonical converter for
    hashcat mode 22000. See plan-knowledge.md § "hcx-tools".
    Handshake and PMKID extraction reuse the same tool: we ask it to
    emit the 22000 hash line for the input pcap; each output line
    encodes signature, PMKID (present when leaked), MAC_AP, MAC_CLIENT,
    ESSID, and the ANONCE/EAPOL blob.
  * scapy — optional (installed via the [pcap] extra). Used for
    `parse_pcap`'s frame-type histogram and IE decode; falls back to
    a plain byte-level parser for radiotap + 802.11 headers when
    scapy is absent so `parse_pcap` still returns a useful summary.
"""

from __future__ import annotations

import asyncio
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

Runner = Callable[[list[str]], "asyncio.Future"]


async def _default_run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout.decode(), stderr.decode()


# --- parse_pcap --------------------------------------------------------------


@dataclass
class PcapSummary:
    total_frames: int
    frame_type_counts: dict[str, int]
    bssids: list[str]
    ssids: list[str]
    clients: list[str]


def _iter_pcap_records(path: Path):
    """Iterate raw frames out of a pcap or pcapng file.

    Classic pcap (magic 0xa1b2c3d4 or 0xd4c3b2a1) is parsed with a
    small byte reader — fast, dependency-free. Pcapng (magic 0x0a0d0d0a)
    hands off to scapy's `rdpcap`, which is a hard project dependency
    (see pyproject.toml [project].dependencies).
    """
    with path.open("rb") as f:
        magic = f.read(4)
        if magic == b"\x0a\x0d\x0d\x0a":
            yield from _iter_pcapng_via_scapy(path)
            return
        if magic == b"\xa1\xb2\xc3\xd4":
            endian = ">"
        elif magic == b"\xd4\xc3\xb2\xa1":
            endian = "<"
        else:
            raise ValueError(f"unknown pcap magic {magic.hex()}")
        # skip the rest of the header: 20 bytes (version/thiszone/sigfigs/snap/link)
        f.read(20)
        while True:
            rec = f.read(16)
            if not rec:
                break
            _ts_s, _ts_us, incl, _orig = struct.unpack(endian + "IIII", rec)
            data = f.read(incl)
            if len(data) != incl:
                break
            yield data


def _iter_pcapng_via_scapy(path: Path):
    """Yield raw 802.11 frame bytes from a pcapng file via scapy.

    scapy handles pcapng blocks, timestamp normalization, and link-type
    detection. We fall back to the raw bytes so the downstream byte
    parser (parse_pcap's frame walk) doesn't care which format the
    file was.
    """
    from scapy.utils import rdpcap  # noqa: PLC0415  # lazy so import cost is scoped

    try:
        packets = rdpcap(str(path))
    except Exception:
        # Malformed / truncated pcapng — return no frames, let the
        # caller decide what "zero frames" means (usually a warning +
        # empty summary).
        return
    for pkt in packets:
        yield bytes(pkt)


def parse_pcap(path: str) -> PcapSummary:
    """Frame-type histogram, unique BSSIDs / SSIDs / clients.

    Byte-level 802.11 parser — good enough for triage. Full IE decode
    lives in the scapy-backed `decode_ies()` (Phase 4+ once the [pcap]
    extra is installed).
    """
    p = Path(path)
    counts: dict[str, int] = {"management": 0, "control": 0, "data": 0, "extension": 0}
    bssids: set[str] = set()
    ssids: set[str] = set()
    clients: set[str] = set()
    total = 0

    for frame in _iter_pcap_records(p):
        total += 1
        radiotap_len = _radiotap_len(frame)
        pkt = frame[radiotap_len:]
        if len(pkt) < 24:
            continue
        fc0 = pkt[0]
        ftype = (fc0 >> 2) & 0x3
        subtype = (fc0 >> 4) & 0xF
        counts[_TYPE_LABELS[ftype]] += 1

        addr1 = _mac(pkt[4:10])
        addr2 = _mac(pkt[10:16])
        addr3 = _mac(pkt[16:22])

        if ftype == 0:  # management
            bssids.add(addr3)
            # addr2 is the sender. In beacons that is the AP (== addr3),
            # in probe requests / assoc requests it is the client.
            if addr2 != addr3 and not _is_broadcast(addr2):
                clients.add(addr2)
            # addr1 is the destination. In probe responses + deauth /
            # disassoc / assoc responses from the AP, addr1 is the
            # unicast client. Broadcast destinations (beacon, broadcast
            # probe request) don't count.
            if addr1 != addr3 and not _is_broadcast(addr1):
                clients.add(addr1)
            if subtype in (0x8, 0x5):  # beacon, probe response
                ssid = _ssid_from_beacon(pkt)
                if ssid:
                    ssids.add(ssid)
        elif ftype == 2:  # data
            bssids.add(addr3)
            if addr1 != addr3:
                clients.add(addr1)
            if addr2 != addr3:
                clients.add(addr2)

    return PcapSummary(
        total_frames=total,
        frame_type_counts=counts,
        bssids=sorted(bssids),
        ssids=sorted(ssids),
        clients=sorted(clients),
    )


_TYPE_LABELS = {0: "management", 1: "control", 2: "data", 3: "extension"}


def _radiotap_len(frame: bytes) -> int:
    if len(frame) < 4 or frame[0] != 0:
        return 0
    return struct.unpack("<H", frame[2:4])[0]


def _mac(b: bytes) -> str:
    return ":".join(f"{x:02x}" for x in b)


def _is_broadcast(mac: str) -> bool:
    return mac == "ff:ff:ff:ff:ff:ff"


def _ssid_from_beacon(pkt: bytes) -> str | None:
    # 802.11 management fixed params (24 header + 12 fixed for beacon)
    i = 24 + 12
    while i + 2 <= len(pkt):
        eid = pkt[i]
        length = pkt[i + 1]
        if i + 2 + length > len(pkt):
            return None
        if eid == 0:  # SSID
            return pkt[i + 2 : i + 2 + length].decode("utf-8", errors="replace")
        i += 2 + length
    return None


# --- hcxpcapngtool-backed extract & convert ---------------------------------


@dataclass
class HashLine22000:
    """One entry from a hashcat mode-22000 line.

    Format (from hashcat wiki):
        WPA*TYPE*PMKID_OR_MIC*MAC_AP*MAC_CLIENT*ESSID_HEX*ANONCE*EAPOL*MESSAGE_PAIR

    TYPE=01 → PMKID-only; TYPE=02 → EAPOL 4-way handshake.
    """

    line: str
    type: str          # "01" (PMKID) or "02" (EAPOL)
    hash_hex: str
    mac_ap: str
    mac_client: str
    essid: str


def _parse_22000(text: str) -> list[HashLine22000]:
    out: list[HashLine22000] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("WPA*"):
            continue
        parts = line.split("*")
        if len(parts) < 6:
            continue
        essid_hex = parts[5]
        try:
            essid = bytes.fromhex(essid_hex).decode("utf-8", errors="replace")
        except ValueError:
            essid = essid_hex
        out.append(
            HashLine22000(
                line=line,
                type=parts[1],
                hash_hex=parts[2],
                mac_ap=_mac_from_hex(parts[3]),
                mac_client=_mac_from_hex(parts[4]),
                essid=essid,
            )
        )
    return out


def _mac_from_hex(h: str) -> str:
    h = h.lower()
    if len(h) != 12:
        return h
    return ":".join(h[i : i + 2] for i in range(0, 12, 2))


async def convert_to_hashcat(
    pcap_path: str,
    out_path: str,
    *,
    hcxpcapngtool: str = "hcxpcapngtool",
    run: Callable[[list[str]], "asyncio.Future"] = _default_run,
) -> dict:
    """Wrap `hcxpcapngtool` to emit a hashcat mode-22000 file.

    Returns {ok, hash_lines, warnings[]}. The caller decides whether
    to keep the raw output file or discard.
    """
    cmd = [hcxpcapngtool, "-o", out_path, pcap_path]
    rc, stdout, stderr = await run(cmd)
    warnings: list[str] = []
    if rc != 0:
        warnings.append(f"hcxpcapngtool exit {rc}: {stderr.strip() or stdout.strip()}")
        return {"ok": False, "hash_lines": [], "warnings": warnings}
    try:
        text = Path(out_path).read_text()
    except FileNotFoundError:
        warnings.append(f"hcxpcapngtool produced no output at {out_path}")
        return {"ok": False, "hash_lines": [], "warnings": warnings}
    return {"ok": True, "hash_lines": _parse_22000(text), "warnings": warnings}


def _split_22000(lines: list[HashLine22000], want_type: str) -> list[HashLine22000]:
    return [h for h in lines if h.type == want_type]


async def extract_handshakes(pcap_path: str, out_path: str, **kw) -> dict:
    """Return only the EAPOL 4-way handshake entries (TYPE=02)."""
    r = await convert_to_hashcat(pcap_path, out_path, **kw)
    r["hash_lines"] = _split_22000(r["hash_lines"], "02")
    return r


async def extract_pmkids(pcap_path: str, out_path: str, **kw) -> dict:
    """Return only the PMKID entries (TYPE=01)."""
    r = await convert_to_hashcat(pcap_path, out_path, **kw)
    r["hash_lines"] = _split_22000(r["hash_lines"], "01")
    return r
