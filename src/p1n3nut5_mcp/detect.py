"""
Pcap parsing and handshake / PMKID extraction.

Phase 0 stub. Local (in the MCP host), so it can run offline against a
downloaded pcap. Will hold:

  * `parse_pcap(path)` — frame-type histogram, unique BSSIDs / SSIDs /
    clients
  * `extract_handshakes(pcap_path)` — EAPOL M1/M2/M3/M4 presence per
    (bssid, client), completeness flag
  * `extract_pmkids(pcap_path)`
  * `decode_ies(bssid_or_pcap)` — human-readable IE breakdown
  * `beacon_diff(bssid_a, bssid_b)` — IE deltas for evil-twin spotting
  * `client_fingerprint(client_mac)` — probe-request-based device guess

scapy is an optional dep (see the [pcap] extra in pyproject.toml).
"""

from __future__ import annotations
