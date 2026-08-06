"""
Parse and enrich recon-DB responses from the Pineapple.

Phase 0 stub. Will hold:

  * normalizers that map WebUI recon payloads into the response shapes
    documented in `records/pineapple_endpoints.json`
    (array-of-{bssid, ssid, channel, rssi, security, last_seen, ies?})
  * IE enrichment — decode RSN, HT/VHT/HE/EHT Capabilities, WPS,
    Vendor-Specific — against `records/ies.json`
  * heuristic filters that back `list_aps(security=…, band=…)`,
    `list_clients(seen_since_s=…)`, `list_probe_requests(client_mac=…)`
"""

from __future__ import annotations
