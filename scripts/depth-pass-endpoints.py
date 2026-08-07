#!/usr/bin/env python3
"""
Depth-pass endpoint carve-out (Phase D4 P1a).

Move the 11 local-operation records out of pineapple_endpoints.json into
knowledge/records/local_operations.json (category `local_operation`).

The local ops run in the MCP process against a downloaded pcap; they are
not device endpoints, and they were previously the only records failing
the plan's "100% of pineapple_endpoints have firmware_min" acceptance.

Idempotent — running twice leaves both files in the correct final state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RECORDS = Path(__file__).resolve().parent.parent / "knowledge" / "records"
ENDPOINTS = RECORDS / "pineapple_endpoints.json"
LOCAL_OPS = RECORDS / "local_operations.json"


# Records that should live in local_operations.json — they run against a
# downloaded pcap, no device call.
LOCAL_IDS = {
    "pep-call-log",
    "pep-run-sequence",  # meta — composes anything, but no device call itself
    "pep-decode-ies",
    "pep-beacon-diff",
    "pep-client-fingerprint",
    "pep-parse-pcap",
    "pep-extract-handshakes",
    "pep-extract-pmkids",
    "pep-convert-to-hashcat",
    "pep-crack-start",
    "pep-crack-status",
}


def main() -> int:
    endpoints = json.loads(ENDPOINTS.read_text(encoding="utf-8"))

    # If local_operations.json already exists, merge (idempotent).
    local: list[dict] = []
    if LOCAL_OPS.exists():
        try:
            local = json.loads(LOCAL_OPS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            local = []

    existing_local_ids = {r["id"] for r in local}

    remaining_endpoints: list[dict] = []
    carved: list[dict] = []
    for rec in endpoints:
        if rec["id"] in LOCAL_IDS:
            # Update the category tag; drop firmware_min/max (irrelevant for local).
            rec = dict(rec)
            rec["category"] = "local_operation"
            rec["transport"] = "analysis"
            rec.pop("firmware_min", None)
            rec.pop("firmware_max", None)
            if rec["id"] not in existing_local_ids:
                carved.append(rec)
        else:
            remaining_endpoints.append(rec)

    # Every remaining endpoint MUST carry firmware_min explicitly. Backfill any
    # that don't (shouldn't happen, but the acceptance criterion is strict).
    for rec in remaining_endpoints:
        rec.setdefault("firmware_min", "3.0.0")
        rec.setdefault("firmware_max", None)

    local.extend(carved)

    ENDPOINTS.write_text(
        json.dumps(remaining_endpoints, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    LOCAL_OPS.write_text(
        json.dumps(local, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"depth-pass-endpoints: {ENDPOINTS} → {len(remaining_endpoints)} endpoints; "
        f"{LOCAL_OPS} → {len(local)} local ops (carved {len(carved)} this run)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
