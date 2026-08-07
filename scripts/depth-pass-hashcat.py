#!/usr/bin/env python3
"""
Depth-pass enrichment for knowledge/records/hashcat_modes.json.

Implements Phase D4 (H1, H2) from plan-improve-docs.md:
  H1. technical_body.example_command on every record — a one-line shell
      invocation with placeholder paths.
  H2. Add `producer_tool` alias field alongside `producer` (plan uses the
      former; corpus uses the latter). Additive, no schema break.

Idempotent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RECORDS = Path(__file__).resolve().parent.parent / "knowledge" / "records"
HASHCAT = RECORDS / "hashcat_modes.json"


EXAMPLE_COMMANDS: dict[str, str] = {
    # Modes (crackable hashes)
    "hashcat-mode-22000": "hashcat -m 22000 hashes.22000 rockyou.txt -w 4 --status",
    "hashcat-mode-22001": "hashcat -m 22001 pmk.22001 pmk_candidates.txt -w 4 --status",
    "hashcat-mode-2500": "hashcat -m 2500 handshake.hccapx rockyou.txt -w 4 --status",
    "hashcat-mode-2501": "hashcat -m 2501 pmk.txt pmk_candidates.txt -w 4",
    "hashcat-mode-16800": "hashcat -m 16800 pmkid.txt rockyou.txt -w 4 --status",
    "hashcat-mode-16801": "hashcat -m 16801 pmk.txt pmk_candidates.txt -w 4",
    "hashcat-mode-5500": "hashcat -m 5500 mschapv2.txt rockyou.txt -w 4 -r rules/best64.rule",
    "hashcat-mode-4800": "hashcat -m 4800 leap.txt rockyou.txt -w 4",
    "hashcat-mode-5300": "hashcat -m 5300 ike-psk-md5.txt rockyou.txt -w 4",
    "hashcat-mode-5400": "hashcat -m 5400 ike-psk-sha1.txt rockyou.txt -w 4",
    "hashcat-mode-7300": "hashcat -m 7300 ipmi.txt rockyou.txt -w 4",
    "hashcat-mode-5600": "hashcat -m 5600 ntlmv2.txt rockyou.txt -w 4 -r rules/best64.rule",
    "hashcat-mode-1000": "hashcat -m 1000 ntlm.txt rockyou.txt -w 4",
    "hashcat-mode-1800": "hashcat -m 1800 shadow.txt rockyou.txt -w 3",
    "hashcat-mode-0": "hashcat -m 0 md5.txt rockyou.txt -w 4",
    "hashcat-mode-100": "hashcat -m 100 sha1.txt rockyou.txt -w 4",
    "hashcat-mode-1400": "hashcat -m 1400 sha256.txt rockyou.txt -w 4",
    "hashcat-mode-1700": "hashcat -m 1700 sha512.txt rockyou.txt -w 4",
    # Attack modes (how to search)
    "hashcat-attack-mode-0": "hashcat -m 22000 -a 0 hs.22000 rockyou.txt -r rules/best64.rule -w 4",
    "hashcat-attack-mode-1": "hashcat -m 22000 -a 1 hs.22000 left.dict right.dict -w 4",
    "hashcat-attack-mode-3": "hashcat -m 22000 -a 3 hs.22000 '?d?d?d?d?d?d?d?d' -w 4",
    "hashcat-attack-mode-6": "hashcat -m 22000 -a 6 hs.22000 rockyou.txt '?d?d?d?d' -w 4",
    "hashcat-attack-mode-7": "hashcat -m 22000 -a 7 hs.22000 '?u?l?l?l' rockyou.txt -w 4",
    "hashcat-attack-mode-9": "hashcat -m 22000 -a 9 hs.22000 rockyou.txt -w 4",
    # Rules / tuning
    "hashcat-rule-best64": "hashcat -m 22000 -a 0 hs.22000 rockyou.txt -r rules/best64.rule -w 4",
    "hashcat-rule-oneruletorulethemall": "hashcat -m 22000 -a 0 hs.22000 rockyou.txt -r rules/OneRuleToRuleThemAll.rule -w 4",
    "hashcat-rule-d3ad0ne": "hashcat -m 22000 -a 0 hs.22000 rockyou.txt -r rules/d3ad0ne.rule -w 4",
    "hashcat-workload-profile": "hashcat -m 22000 -a 0 hs.22000 rockyou.txt -w 4 -O",
    "hashcat-session-restore": "hashcat --session=defcon32 -m 22000 -a 0 hs.22000 rockyou.txt ; hashcat --session=defcon32 --restore",
    "hashcat-slow-hash-warning": "hashcat -m 22000 -a 0 hs.22000 rockyou.txt -w 4 --status --status-timer=30",
}


# Records that have a `producer` key gain a duplicate `producer_tool` key.
# This is the additive alias the plan expects; new code can key on either.
def add_producer_alias(rec: dict) -> None:
    tb = rec.get("technical_body", {})
    if "producer" in tb and "producer_tool" not in tb:
        tb["producer_tool"] = tb["producer"]


def apply(records: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in records}
    for rid, cmd in EXAMPLE_COMMANDS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        tb = rec.setdefault("technical_body", {})
        if not tb.get("example_command"):
            tb["example_command"] = cmd
    for r in records:
        add_producer_alias(r)
        # Guarantee the field is present, even if empty (schema uniformity).
        tb = r.setdefault("technical_body", {})
        tb.setdefault("example_command", "")
    return records


def main() -> int:
    data = json.loads(HASHCAT.read_text(encoding="utf-8"))
    data = apply(data)
    HASHCAT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"depth-pass-hashcat: wrote {HASHCAT} — {len(data)} records", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
