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


# --- scapy-backed IE / beacon / fingerprint tools ---------------------------


def _iter_scapy_beacons(pcap_path: str):
    """Yield scapy 802.11 beacon packets from `pcap_path` (pcap or pcapng)."""
    from scapy.layers.dot11 import Dot11Beacon  # noqa: PLC0415
    from scapy.utils import rdpcap  # noqa: PLC0415

    for pkt in rdpcap(pcap_path):
        if pkt.haslayer(Dot11Beacon):
            yield pkt


def _iter_scapy_probe_requests(pcap_path: str):
    """Yield scapy Dot11ProbeReq / Dot11AssoReq packets."""
    from scapy.layers.dot11 import Dot11AssoReq, Dot11ProbeReq  # noqa: PLC0415
    from scapy.utils import rdpcap  # noqa: PLC0415

    for pkt in rdpcap(pcap_path):
        if pkt.haslayer(Dot11ProbeReq) or pkt.haslayer(Dot11AssoReq):
            yield pkt


def _walk_ies(pkt) -> dict[int, str]:
    """Walk a scapy 802.11 management packet's IEs → {element_id: hex bytes}.

    Handles both `Dot11Elt` (opaque info bytes) and its structured
    subclasses (`Dot11EltRSN`, `Dot11EltVendorSpecific`, `Dot11EltRates`,
    …). For subclasses that set `info = None` we serialize the layer
    body via `bytes(layer)[2:]` — the same on-the-wire IE body bytes,
    just recovered after scapy's structured dissection.
    """
    from scapy.layers.dot11 import Dot11Elt  # noqa: PLC0415

    ies: dict[int, str] = {}
    layer = pkt.getlayer(Dot11Elt)
    while layer is not None:
        eid = int(layer.ID)
        info = getattr(layer, "info", None)
        if info is not None:
            body = bytes(info)
        else:
            # Structured IE subclass: recover raw body from serialized form.
            # bytes(layer) includes children after this IE, so we split
            # by taking exactly `len` bytes past the 2-byte header.
            raw = bytes(layer)
            length = raw[1] if len(raw) >= 2 else 0
            body = raw[2 : 2 + length]
        # First occurrence wins — Vendor IE (0xdd) repeats per-vendor; the
        # caller can re-parse the frame with scapy for full granularity.
        ies.setdefault(eid, body.hex())
        # Follow the IE chain via .payload (scapy links Dot11Elt subclasses
        # via payload, not by getlayer(Dot11Elt) which returns the same
        # match repeatedly).
        nxt = layer.payload if layer.payload else None
        if nxt is None or type(nxt).__name__ == "NoPayload":
            break
        layer = nxt.getlayer(Dot11Elt) if hasattr(nxt, "getlayer") else None
        if layer is None:
            break
    return ies


def _bssid_of(pkt) -> str | None:
    from scapy.layers.dot11 import Dot11  # noqa: PLC0415

    d = pkt.getlayer(Dot11)
    if d is None:
        return None
    b = d.addr3
    return b.lower() if b else None


def decode_ies(pcap_path: str) -> dict:
    """Return `{bssid: {element_id: hex_bytes}}` for every beacon in `pcap_path`.

    Uses scapy's `Dot11Elt` walker; supports classic pcap and pcapng.
    Deterministic ordering by first-observed IE. WCTF beacon-flag-stego
    subgenre depends on byte-level IE inspection.
    """
    out: dict[str, dict[int, str]] = {}
    for pkt in _iter_scapy_beacons(pcap_path):
        bssid = _bssid_of(pkt)
        if bssid is None:
            continue
        out.setdefault(bssid, _walk_ies(pkt))
    return {"ok": True, "payload": out}


def beacon_diff(bssid_a: str, bssid_b: str, pcap_path: str) -> dict:
    """Diff the IE sets of the first beacon from each BSSID in `pcap_path`.

    Returns
        {only_in_a: [element_ids], only_in_b: [...], different: {eid: (a_hex, b_hex)}}
    The evil-twin-farm triage primitive: near-identical beacons that
    differ in one Vendor IE byte or an RSN cipher-suite selector are
    the odd one out.
    """
    a_want = bssid_a.lower()
    b_want = bssid_b.lower()
    a_ies: dict[int, str] | None = None
    b_ies: dict[int, str] | None = None
    for pkt in _iter_scapy_beacons(pcap_path):
        bssid = _bssid_of(pkt)
        if bssid == a_want and a_ies is None:
            a_ies = _walk_ies(pkt)
        elif bssid == b_want and b_ies is None:
            b_ies = _walk_ies(pkt)
        if a_ies is not None and b_ies is not None:
            break
    if a_ies is None or b_ies is None:
        missing = [b for b, ies in ((bssid_a, a_ies), (bssid_b, b_ies)) if ies is None]
        return {
            "ok": False,
            "payload": None,
            "warnings": [f"no beacon in {pcap_path} for BSSIDs: {missing}"],
        }
    only_a = sorted(set(a_ies) - set(b_ies))
    only_b = sorted(set(b_ies) - set(a_ies))
    different = {
        eid: (a_ies[eid], b_ies[eid])
        for eid in sorted(set(a_ies) & set(b_ies))
        if a_ies[eid] != b_ies[eid]
    }
    return {
        "ok": True,
        "payload": {
            "only_in_a": only_a,
            "only_in_b": only_b,
            "different": different,
        },
    }


def client_fingerprint(client_mac: str, pcap_path: str) -> dict:
    """Stable fingerprint for `client_mac` from its probe / assoc requests.

    Hash of the client's IE-order + capability-info bits. Matches
    `records/client_fingerprints.json` entries when possible: if the
    fingerprint hex equals one of the corpus records'
    `technical_body.signature`, return that record's id in the payload.

    Returns
        {ok, payload: {fingerprint, matches?, ie_order, capabilities}, warnings}
    """
    import hashlib  # noqa: PLC0415

    want = client_mac.lower()
    ie_order: list[int] | None = None
    caps: int | None = None
    for pkt in _iter_scapy_probe_requests(pcap_path):
        # addr2 is the client (source) for probe / assoc requests
        d = pkt.getlayer("Dot11")
        if d is None or (d.addr2 or "").lower() != want:
            continue
        ies = _walk_ies(pkt)
        ie_order = list(ies.keys())
        caps = int(getattr(pkt, "cap", 0) or 0)
        break
    if ie_order is None:
        return {
            "ok": False,
            "payload": None,
            "warnings": [f"no probe/assoc request for {client_mac} in {pcap_path}"],
        }
    material = ",".join(str(i) for i in ie_order) + f"|cap={caps}"
    fp = hashlib.sha256(material.encode()).hexdigest()[:16]
    matches = _match_client_fingerprint(fp)
    return {
        "ok": True,
        "payload": {
            "fingerprint": fp,
            "ie_order": ie_order,
            "capabilities": caps,
            "matches": matches,
        },
    }


def _match_client_fingerprint(fp: str) -> str | None:
    """Look up `fp` against records/client_fingerprints.json."""
    from p1n3nut5_mcp import knowledge as _kb  # noqa: PLC0415

    corpus = _kb.get_corpus()
    for rec in corpus.category("client_fingerprint"):
        sig = rec.body.get("technical_body", {}).get("signature")
        if sig == fp:
            return rec.id
    return None
