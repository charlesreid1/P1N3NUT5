"""
Composed attack sequences.

Phase 0 stub. Sits above `pineapple_api` / `pineapple_ssh` and
composes primitives into the higher-level actions the assistant reaches
for at a WCTF:

  * `capture_handshake(bssid, …)` — airodump + optional targeted deauth
  * `capture_pmkid(bssid?, …)` — hcxdumptool with the ESSID filter
  * `evil_twin(target_bssid, options?)` — clone SSID/BSSID/channel,
    optionally deauth clients off the real AP to force reassociation
  * `serve_captive_portal(handle, template=…)` — captive portal in
    front of a rogue AP
  * `rogue_radius(…)` — mock RADIUS to capture EAP-MSCHAPv2 pairs
  * `run_sequence(steps)` — the WiFi analog of PHR34CKER5's
    `play_sequence`; the scripted-engagement orchestrator

Every attack refuses cleanly (with citation) when preconditions are
violated — e.g. `deauth` against a PMF-required target — per the
`explain_attack` never-refuse rule combined with the safety envelope in
plan-organize.md ("Legal & consent").
"""

from __future__ import annotations
