#!/usr/bin/env python3
"""
Depth-pass enrichment for knowledge/records/eap_methods.json.

Implements Phase D3 (E1) from plan-improve-docs.md:
  E1. Populate technical_body.attacks[] on every EAP method record with
      the attacks.json ids that target that method or leverage it.

Idempotent. Only adds ids the caller lists; never overwrites author-authored
attacks[] arrays.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RECORDS = Path(__file__).resolve().parent.parent / "knowledge" / "records"
EAP = RECORDS / "eap_methods.json"


# Every entry is a list of attacks.json ids that either name this EAP method
# in `target_security`, in `see_also`, or in the notes/prose flow. If a
# method has no direct attack surface (SIM/AKA/AKA-prime), the value is [] —
# schema stays uniform, semantically means "no known direct-attack record."
BACKREFS: dict[str, list[str]] = {
    "eap-md5": [
        "mschapv2-challenge-response-capture",  # captured challenge/response class shares crack path
        "rogue-radius-hostapd-wpe",             # rogue RADIUS accepts everything on no-mutual-auth methods
    ],
    "eap-leap": [
        "leap-legacy-crack",
        "asleap-mschapv2-crack",
    ],
    "eap-tls": [
        "cert-phish-eaphammer-weak-validation",
        "mdm-profile-theft-captive-portal",
    ],
    "eap-ttls": [
        "rogue-radius-hostapd-wpe",
        "rogue-radius-eaphammer",
        "cert-phish-eaphammer-weak-validation",
    ],
    "eap-peap": [
        "rogue-radius-hostapd-wpe",
        "rogue-radius-eaphammer",
        "cert-phish-eaphammer-weak-validation",
        "eap-inner-downgrade-peap-mschapv2",
        "eap-inner-downgrade-peap-gtc",
    ],
    "eap-fast": [
        "rogue-radius-eaphammer",
        "cert-phish-eaphammer-weak-validation",
    ],
    "eap-pwd": [
        "dragonblood-sidechannel",
        "dragonblood-timing",
    ],
    "eap-sim": [
        # Not directly cracked, but a rogue RADIUS accepts SIM triplets it did
        # not derive when the client omits mutual auth — leaks IMSI + SRES.
        "rogue-radius-eaphammer",
    ],
    "eap-aka": [
        "rogue-radius-eaphammer",
    ],
    "eap-gtc": [
        "eap-inner-downgrade-peap-gtc",
        "eap-gtc-plaintext-token-capture",
    ],
    "eap-peap-mschapv2": [
        "eap-inner-downgrade-peap-mschapv2",
        "mschapv2-challenge-response-capture",
        "hashcat-5500-mschapv2-crack",
        "asleap-mschapv2-crack",
        "rogue-radius-hostapd-wpe",
    ],
    "eap-peap-gtc": [
        "eap-inner-downgrade-peap-gtc",
        "eap-gtc-plaintext-token-capture",
    ],
    "eap-ttls-pap": [
        "rogue-radius-eaphammer",
        "rogue-radius-hostapd-wpe",
    ],
    "eap-ttls-chap": [
        "rogue-radius-eaphammer",
        "mschapv2-challenge-response-capture",
    ],
    "eap-ttls-mschapv2": [
        "rogue-radius-hostapd-wpe",
        "rogue-radius-eaphammer",
        "mschapv2-challenge-response-capture",
        "hashcat-5500-mschapv2-crack",
        "asleap-mschapv2-crack",
    ],
    "eap-fast-mschapv2": [
        "rogue-radius-eaphammer",
        "mschapv2-challenge-response-capture",
        "hashcat-5500-mschapv2-crack",
    ],
    "eap-fast-gtc": [
        "rogue-radius-eaphammer",
        "eap-gtc-plaintext-token-capture",
    ],
    "eap-tls-1-3": [
        "cert-phish-eaphammer-weak-validation",
        "mdm-profile-theft-captive-portal",
    ],
    "eap-ikev2": [
        # PSK-mode IKEv2 (rare on WiFi) is offline-crackable via hashcat 5300/5400.
        "hashcat-5500-mschapv2-crack",
    ],
    "eap-eke": [
        # PAKE-based — if a rogue AP negotiates a weak group, offline surface exists.
        "dragonblood-modp-downgrade",
    ],
    "eap-noob": [
        # Out-of-band commissioning; rogue RADIUS surface exists during the
        # initial online completion phase.
        "rogue-radius-eaphammer",
    ],
    "eap-otp": [
        "rogue-radius-hostapd-wpe",
        "eap-gtc-plaintext-token-capture",
    ],
    "eap-mschapv2-outer": [
        "mschapv2-challenge-response-capture",
        "hashcat-5500-mschapv2-crack",
        "asleap-mschapv2-crack",
    ],
    "eap-aka-prime": [
        "rogue-radius-eaphammer",
    ],
    "eap-ttlsv1": [
        "rogue-radius-eaphammer",
    ],
    "eap-teap": [
        "rogue-radius-eaphammer",
        "cert-phish-eaphammer-weak-validation",
    ],
    "eap-identity": [
        "anqp-realm-enum",  # not an EAP attack per se but the identity realm leak is the same primitive class
    ],
    "eap-request-notification": [
        # Notification frames are informational — attack surface is spoofing them
        # to socially engineer a supplicant. Cover via the eaphammer flow.
        "rogue-radius-eaphammer",
    ],
    "eap-request-nak": [
        "eap-inner-downgrade-peap-mschapv2",
        "eap-inner-downgrade-peap-gtc",
    ],
    "eap-expanded-nak": [
        "eap-inner-downgrade-peap-mschapv2",
        "eap-inner-downgrade-peap-gtc",
    ],
}


def apply(records: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in records}
    for rid, ids in BACKREFS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        tb = rec.setdefault("technical_body", {})
        existing = list(tb.get("attacks") or [])
        merged: list[str] = []
        seen: set[str] = set()
        for a in existing + ids:
            if a in seen:
                continue
            seen.add(a)
            merged.append(a)
        tb["attacks"] = merged
    # Every EAP method must have the field, even if empty.
    for r in records:
        tb = r.setdefault("technical_body", {})
        tb.setdefault("attacks", [])
    return records


def main() -> int:
    data = json.loads(EAP.read_text(encoding="utf-8"))
    data = apply(data)
    EAP.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"depth-pass-eap: wrote {EAP} — {len(data)} records", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
