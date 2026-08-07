#!/usr/bin/env python3
"""
Generate knowledge/records/channels.json.

The channel table is pure regulatory data (frequencies, DFS/TPC flags,
per-region allowance) — mechanical, not judgment-heavy, so we author
it deterministically here rather than hand-typing 150 near-identical
records. The FCC / ETSI / MIC references cited in each record are
still the authority; this generator encodes the same tables.

Output: knowledge/records/channels.json — a JSON array of records,
one per (channel, band, region-of-primary-interest) that the plan
declares in its ontology.

Run whenever the regulatory tables update. The file itself is
committed; this script is the seed.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "knowledge" / "records" / "channels.json"

CITES_2G4 = ["ieee-802-11-2020", "fcc-part-15", "etsi-en-300-328"]
CITES_5G = ["fcc-part-15", "etsi-en-301-893"]
CITES_6G = ["fcc-part-15", "wfa-wpa3-6ghz-mandate"]


# ---- 2.4 GHz ---------------------------------------------------------------

CH_2G4 = list(range(1, 15))  # 1..14
def freq_2g4(ch: int) -> int:
    return 2484 if ch == 14 else 2407 + 5 * ch


def region_2g4(ch: int) -> dict[str, str]:
    if ch == 14:
        return {"US": "forbidden", "EU": "forbidden", "JP": "802.11b only"}
    if ch in (12, 13):
        return {"US": "forbidden", "EU": "allowed", "JP": "allowed"}
    return {"US": "allowed", "EU": "allowed", "JP": "allowed"}


def region_top_2g4(ch: int) -> str:
    if ch == 14:
        return "JP"
    if ch in (12, 13):
        return "EU"
    return "universal"


# ---- 5 GHz -----------------------------------------------------------------

# (channel, unii sub-band). US assignments (802.11-2020 §17 + FCC Part 15
# subpart E). EU aligns on 36..64 + 100..140; JP on 36..64.
UNII1 = [36, 40, 44, 48]            # 5170..5250, no DFS/TPC
UNII2A = [52, 56, 60, 64]           # 5250..5330, DFS+TPC
UNII2C = list(range(100, 145, 4))   # 100..144, DFS+TPC
UNII3 = [149, 153, 157, 161, 165]   # 5735..5835, no DFS/TPC (US)


def freq_5g(ch: int) -> int:
    return 5000 + 5 * ch


def unii_5g(ch: int) -> str:
    if ch in UNII1:
        return "UNII-1"
    if ch in UNII2A:
        return "UNII-2A"
    if ch in UNII2C:
        return "UNII-2C"
    if ch in UNII3:
        return "UNII-3"
    return "unknown"


def dfs_5g(ch: int) -> bool:
    return ch in UNII2A or ch in UNII2C


def region_5g(ch: int) -> dict[str, str]:
    if ch in UNII1:
        return {"US": "allowed", "EU": "allowed", "JP": "allowed"}
    if ch in UNII2A or ch in UNII2C:
        return {"US": "allowed (DFS+TPC)", "EU": "allowed (DFS+TPC)", "JP": "allowed (DFS+TPC)"}
    if ch in UNII3:
        if ch == 165:
            return {"US": "allowed (20 MHz only)", "EU": "forbidden", "JP": "forbidden"}
        return {"US": "allowed", "EU": "restricted (max power)", "JP": "forbidden"}
    return {"US": "?", "EU": "?", "JP": "?"}


def region_top_5g(ch: int) -> str:
    if ch in UNII3:
        return "US"
    return "universal"


def widths_5g(ch: int) -> list[int]:
    if ch == 165:
        return [20]
    return [20, 40, 80, 160]


# ---- 6 GHz (Wi-Fi 6E / 7) --------------------------------------------------

# US 6 GHz: channels 1..233, spacing 4, center = 5950 + 5*ch (MHz).
# UNII-5: 1..93   (5945..6425)
# UNII-6: 97..113 (6445..6525)
# UNII-7: 117..185(6545..6865)
# UNII-8: 189..233(6885..7085)
# Every 6 GHz channel is WPA3-only per Wi-Fi Alliance CERTIFIED 6E.

def freq_6g(ch: int) -> int:
    return 5950 + 5 * ch


def unii_6g(ch: int) -> str:
    if 1 <= ch <= 93:
        return "UNII-5"
    if 97 <= ch <= 113:
        return "UNII-6"
    if 117 <= ch <= 185:
        return "UNII-7"
    if 189 <= ch <= 233:
        return "UNII-8"
    return "unknown"


def region_6g(ch: int) -> dict[str, str]:
    # Full US allocation; EU only 5945..6425 (UNII-5).
    if 1 <= ch <= 93:
        return {"US": "LPI/SP/VLP tiers", "EU": "LPI only (5945–6425)"}
    return {"US": "LPI/SP/VLP tiers", "EU": "not allocated"}


def region_top_6g(ch: int) -> str:
    return "US"


# ---- records ---------------------------------------------------------------


def rec_2g4(ch: int) -> dict:
    notes = None
    if ch == 1:
        notes = "Non-overlapping with 6 and 11 at 20 MHz. Overlapping at 40 MHz."
    elif ch == 11:
        notes = "Highest US channel — 12 and 13 are EU/JP only; 14 is JP-only 802.11b at 2484 MHz."
    body = {
        "band_ghz": 2.4,
        "channel": ch,
        "center_mhz": freq_2g4(ch),
        "widths_mhz": [22] if ch == 14 else [20, 40],
        "regulatory": region_2g4(ch),
        "dfs_required": False,
        "tpc_required": False,
    }
    if notes:
        body["notes"] = notes
    if ch == 14:
        body["widths_mhz"] = [22]
    r = {
        "id": f"ch-2g4-{ch}",
        "name": f"2.4 GHz channel {ch}" + (" (EU/JP)" if ch in (12, 13) else "" if ch != 14 else " (JP 802.11b only)"),
        "category": "band_and_channel",
        "region": region_top_2g4(ch),
        "era_bounds": ["1999", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": CITES_2G4,
        "technical_body": body,
    }
    return r


def rec_5g(ch: int) -> dict:
    body = {
        "band_ghz": 5,
        "channel": ch,
        "center_mhz": freq_5g(ch),
        "widths_mhz": widths_5g(ch),
        "unii_subband": unii_5g(ch),
        "regulatory": region_5g(ch),
        "dfs_required": dfs_5g(ch),
        "tpc_required": dfs_5g(ch),
    }
    if dfs_5g(ch) and ch == 52:
        body["notes"] = "DFS radar-avoidance mandatory. Radios must vacate on radar detection."
    return {
        "id": f"ch-5-{ch}-{unii_5g(ch).lower()}",
        "name": f"5 GHz channel {ch} ({unii_5g(ch)})",
        "category": "band_and_channel",
        "region": region_top_5g(ch),
        "era_bounds": ["1999" if ch <= 64 else "2003", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": CITES_5G,
        "technical_body": body,
    }


def rec_6g(ch: int) -> dict:
    body = {
        "band_ghz": 6,
        "channel": ch,
        "center_mhz": freq_6g(ch),
        "widths_mhz": [20, 40, 80, 160, 320],
        "unii_subband": unii_6g(ch),
        "regulatory": region_6g(ch),
        "wpa3_only": True,
    }
    if ch == 1:
        body["notes"] = "6 GHz mandates WPA3-Personal or WPA3-Enterprise; no WPA2 downgrade."
    elif ch == 233:
        body["notes"] = "Highest US 6 GHz channel — 7115 MHz center. Above this is not FCC-allocated."
    return {
        "id": f"ch-6-{ch}-{unii_6g(ch).lower()}",
        "name": f"6 GHz channel {ch} ({unii_6g(ch)})",
        "category": "band_and_channel",
        "region": region_top_6g(ch),
        "era_bounds": ["2020", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": CITES_6G,
        "technical_body": body,
    }


def main() -> None:
    records: list[dict] = []

    # 2.4 GHz — all 14 channels
    for ch in CH_2G4:
        records.append(rec_2g4(ch))

    # 5 GHz UNII-1 / -2A / -2C / -3
    for ch in UNII1 + UNII2A + UNII2C + UNII3:
        records.append(rec_5g(ch))

    # 6 GHz UNII-5 / -6 / -7 / -8 — every 4th channel from 1..233
    for ch in range(1, 234, 4):
        records.append(rec_6g(ch))

    # Dedupe by id (the special anchor records have ids like
    # ch-5-36-unii1 not ch-5-36 — keep the anchor form).
    by_id: dict[str, dict] = {}
    for r in records:
        by_id[r["id"]] = r

    out = sorted(by_id.values(), key=lambda r: r["id"])
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} channel records to {OUT}")


if __name__ == "__main__":
    main()
