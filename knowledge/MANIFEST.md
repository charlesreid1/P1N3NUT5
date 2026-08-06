# P1N3NUT5 CORPUS — MANIFEST

This directory is the **reference half** of P1N3NUT5 — the reservoir of
802.11 / WPA2 / WPA3 / EAP / hardware / attack knowledge the assistant
consults to advise. The **acting half** lives in [`src/`](../src/):
the MCP tools that drive a Hak5 WiFi Pineapple Mark VII (recon,
PineAP, rogue AP, deauth, capture) and analyze what came back
(handshake extraction, PMKID, hashcat handoff). A good WCTF answer
usually draws on both — look up the frame layout / cipher / hashcat
mode here, then act on it from `src/`.

The prose here is the half you *read*. Alongside it,
[`records/`](records/) is a typed, dated, cited knowledge repository —
the half you *look facts up in* (RSN AKM selector bytes, exact channel
regulatory status, hashcat mode numbers, CVE→attack→mitigation chains).
The retrieval tools (`lookup_standard`, `lookup_channel`, `lookup_frame`,
`lookup_ie`, `lookup_cipher`, `lookup_eap`, `lookup_attack`,
`lookup_cve`, `lookup_hashcat_mode`, `verify_claim`, `explain_attack`,
`bibliography`, `cross_reference`, `search_records`) bind to those JSON
records, not to free text. See [`records/README.md`](records/README.md).

Every `.md` file below is exposed as an MCP resource under
`p1n3nut5://<topic>/<name>` and is searchable via the `search_lore`
tool. Add files freely; the server picks them up on next startup.

Phase 0 has authored none of the topic files below. Phase 2 in
plan-organize.md is the load-bearing pass that fills them in, in the
tier order laid out in plan-knowledge.md.

## Topics (planned — see plan-knowledge.md for tier order)

### Tier 1 — modern workhorses

- **802.11/**            — how a modern WiFi session works end-to-end
- **wpa2/**              — WPA2-PSK / WPA2-Enterprise, 4-way handshake byte-by-byte
- **wpa3/**              — SAE (Dragonfly), H2E, transition mode, PMF-required
- **pmkid/**             — Steube 2018, hashcat mode 22000 with only M1
- **4-way-handshake/**   — capture / convert / crack across every corner case
- **deauth/**            — the 26-byte frame, reason codes, PMF interaction
- **evil-twin/**         — clone SSID+BSSID+channel, force reassociation
- **pineap/**            — what the Mark VII's PineAP module does
- **captive-portal/**    — the WCTF favorite; DHCP → DNS → HTTP → login
- **hashcat/**           — the crack side of the game; mode reference

### Tier 2 — historical-but-alive

- **wep/**, **wps/**, **krack/**, **fragattacks/**, **dragonblood/**,
  **802.1x-eap/**

### Tier 3 — hardware / OpenWRT

- **pineapple-mk7/**, **openwrt/**, **hostapd/**, **hcx-tools/**

### Tier 4 — perception & analysis

- **pcap/**, **fingerprinting/**, **ies/**

### Tier 5 — CTF-facing (P1N3NUT5 analog of PHR34CKER5's ctf/)

- **ctf/**               — one file per WCTF puzzle subgenre:
  hidden-ssid-mazes, pmf-required-targets, wpa2-crack-flags,
  wpa3-transition-downgrade, evil-twin-farms,
  captive-portal-cred-flags, pmkid-fastpath, beacon-flag-stego,
  probe-request-flag, deauth-forensics, rogue-radius-eap-flag,
  wps-pin-flag

### Tier 6 — glossary and orientation

- **glossary/**, **zines-and-talks/**

## Conventions

- One idea per file. Keep files short and cite sources at the bottom.
- Filename slug is lowercase-with-dashes and becomes the resource name.
- Prefer plain markdown. ASCII art welcome. Do not embed binaries.
- Per-topic files, as they earn their keep (from plan-knowledge.md):
  - `README.md` — orient; what is this, why care. Short.
  - `reference.md` — the technical spec; frame layouts, cipher
    parameters, hashcat modes, exact fields. Dry, complete,
    load-bearing.
  - `walkthrough.md` — worked examples. Real traffic hints at each step.
    Time-annotated. Failure modes.
  - `recognition.md` — how to identify this thing on the air / in a
    pcap. WCTF triage layer.
  - `history.md` — optional. The full story — landmark papers,
    first-published exploits, timeline.
- Every `reference.md` cites at least one primary source at the bottom.
  Same discipline as PHR34CKER5: no primary cite, no record loads.
- History is context, not the center. Wireless is a story of **layered
  survival**, not **replaced era**: WEP is 25 years old but still
  ships on industrial embedded; WPS lingers on consumer routers; WPA2
  4-way capture is still the primary DEFCON WCTF workhorse. Every
  record carries `era_bounds` and a `still_effective_2026` flag —
  see plan-knowledge.md for the guiding rule.
