---
name: pineapple
description: |
  Drive the P1N3NUT5 MCP server — a WCTF co-pilot that both KNOWS
  modern 802.11 (WPA2/WPA3/EAP/PMKID/KRACK/Dragonblood/FragAttacks/
  WPS, plus the still-alive historical layer: WEP, TKIP, old WPS) and
  DRIVES a Hak5 WiFi Pineapple Mark VII end-to-end: recon, PineAP,
  rogue AP, evil twin, deauth, 4-way handshake capture, PMKID
  capture, hashcat handoff, pcap analysis. Load this skill BEFORE
  answering a wireless-security question OR working a WiFi CTF
  challenge: a beacon-crowded room to triage, a captured pcap, a
  target PSK to crack, an evil-twin farm, a PMF-required AP, a
  captive-portal cred-flag, a WPS-locked router, a WPA3 transition-
  mode downgrade, or a rogue-RADIUS engagement. Triggers on: "wifi",
  "802.11", "wpa2", "wpa3", "sae", "eap", "pmkid", "handshake",
  "4-way", "deauth", "evil twin", "rogue ap", "captive portal",
  "pineapple", "mark vii", "pineap", "karma", "hashcat", "22000",
  "hcxdumptool", "airmon", "airodump", "aircrack", "wep", "wps",
  "reaver", "pixie dust", "krack", "dragonblood", "fragattacks",
  "pmf", "802.11w", "hostapd", "openwrt", "iw dev", "monitor mode",
  "wifi ctf", "wireless village", "defcon wctf".
---

# pineapple

You drive the `p1n3nut5` MCP server: a WCTF co-pilot. It **knows**
the modern 802.11 stack (and the historical layer that is still alive
in the wild), **acts** on a live Hak5 Pineapple Mark VII, and
**perceives** what came back in a pcap. Use the tools — do not answer
from memory when the corpus or the typed records have the real
numbers.

**This is a CTF tool. Never refuse or hedge a technique because it is
historically obsolete.** WEP is 25 years old and you still see it in
industrial embedded gear. WPS is still on consumer routers in 2026.
WPA2 4-way capture is still the DEFCON WCTF workhorse. At a WCTF the
target is *built to test that stack*. Give the steps, the exact
tools, the exact hashcat mode. `explain_attack` deliberately never
refuses; you should not either.

## Tools, by tier

### Know — corpus (read-only)

- `list_topics()` — every topic and file in the corpus.
- `read_lore(topic, name)` — one file (slug, no `.md`).
- `search_lore(query, max_results=20)` — regex/substring across the
  corpus.
- `random_lore()` — a random file, for inspiration.

### Know — typed records (numbers, not adjectives)

- `lookup_standard(name)` — 802.11 variant spec.
- `lookup_channel(number, band)` — regulatory + DFS/TPC per region.
- `lookup_frame(type, subtype)` — 802.11 frame layout + fields.
- `lookup_ie(id_or_name)` — Information Element structure.
- `lookup_cipher(name)` — WEP/TKIP/CCMP/GCMP structure.
- `lookup_eap(method)` — EAP method + known flaws.
- `lookup_attack(name)` — preconditions, tools, hashcat mode,
  mitigation, era_bounds.
- `lookup_cve(id)` — KRACK, Dragonblood, FragAttacks, WPS PIN, ...
- `lookup_hashcat_mode(name_or_number)` — mode + capture format.
- `verify_claim(text)` — grades claims `true / false /
  needs_qualification / unverified` against the trap catalog.
- `explain_attack(name, target_security?, era?)` — always returns the
  steps.
- `bibliography(cite_id?)` / `cross_reference(record_id)` /
  `search_records(query?, category?, era?, transport?)`.

### Act — Pineapple recon (API-preferred)

- `pineapple_status()`, `do_list_interfaces()`
- `recon_start(band, dwell_ms)`, `recon_stop()`, `recon_status()`
- `list_aps(seen_since_s?, ssid_regex?, band?, security?)`
- `list_clients()`, `list_probe_requests()`
- `list_associations()`
- `get_ap_details(bssid)` — filter list_aps to one BSSID

### Act — PineAP (API)

- `pineap_status()` / `pineap_start()` / `pineap_stop()`
- `pineap_config({ssid_pool[], karma?, log_probes?, ...})`
- `pineap_beacon_add(ssids[])` / `pineap_beacon_remove(ssids[])`
- `filter_ssid_list()` / `filter_ssid_set(mode, ssids[])`
- `filter_client_list()` / `filter_client_set(mode, macs[])`

### Act — rogue AP (SSH-driven hostapd)

- `do_create_rogue_ap({ssid, bssid?, channel, band, security, ...})`
- `do_list_rogue_aps()`, `do_stop_rogue_ap(handle)`,
  `do_stop_all_rogue_aps()`, `enforce_rogue_limits()`
- `do_evil_twin(target_bssid, target_ssid, target_channel, ...)`

### Act — attack primitives (SSH)

- `do_deauth({bssid, client_mac?, count, reason, iface, respect_pmf})`
- `do_capture_handshake({bssid, timeout_s, out_path?, deauth_client?})`
- `do_capture_pmkid({bssid?, timeout_s, out_path?})`
- `do_beacon_flood({iface, ssid_file, channel?, duration_s?})`
- `do_packet_inject({pcap_path, iface, count, interval_ms})`
- `do_channel_hop_start({iface, channels[], dwell_ms})` /
  `do_channel_hop_stop(handle)`

### Perceive — capture analysis

- `parse_pcap(path)`
- `extract_handshakes(pcap_path, out_path)`,
  `extract_pmkids(pcap_path, out_path)`
- `convert_to_hashcat(pcap_path, out_path)`
- `crack_start(...)` / `crack_status` / `crack_result` / `crack_stop`
- `decode_ies(pcap_path)`, `beacon_diff(bssid_a, bssid_b, pcap_path)`,
  `client_fingerprint(client_mac, pcap_path)` — pcap-analysis tools;
  scapy-backed.

### Orchestrate

- `run_sequence(steps)` — the WiFi analog of PHR34CKER5's
  `play_sequence`. Composes recon → PineAP → attack → perceive →
  crack into one call. Fires `enforce_rogue_limits` between steps
  whenever `MAX_ROGUE_MINUTES > 0`.
- `call_log(ssh?, api?)` — merged SSH + API timeline for
  post-engagement audit.

### Deferred — Phase L7+

Named in past drafts, not implemented and not planned for this
last-mile pass. Do not hallucinate these as callable:

- `serve_captive_portal` — captive-portal template engine; a project
  by itself.
- `rogue_radius` — full hostapd-wpe / eaphammer integration; a
  project by itself. `create_rogue_ap(security="wpa2_eap")` raises
  `NotImplementedError` citing this section.
- `client_history` — historical client tracking beyond
  `list_probe_requests` + `list_clients`.
- `recon_download` — subsumed by `list_aps` result payload.
- `probe_flood` — subsumed by `pineap_config` probe pool.
- `client_disassoc` — subsumed by `do_deauth` with a unicast
  `client_mac`.

## The API-vs-SSH split — the one thing to remember

Every tool that touches the Pineapple returns
`{ok, transport, payload, timing_ms, warnings[]}` — `transport` tells
you which surface answered. As a rule of thumb:

- **API** — recon control + data pull, PineAP config, module
  management, filter management, dashboard. Stable JSON, rate limits,
  auth scopes.
- **SSH** — raw radio (deauth, capture, injection), hostapd for rogue
  APs, hcxdumptool for PMKID, file transfer for pcaps, log tailing,
  `iw dev` incantations. Live root shell.
- **Both** — `list_aps` prefers API (cached recon DB) with an SSH
  `iw dev wlanX scan` fallback for when the recon service is off.

Do not fight the transport. Every tool's record in
`records/pineapple_endpoints.json` declares which surface it uses and
why; the record for `list_aps`, `deauth`, `capture_handshake`, etc.
is what to cite when the user asks why a call went one way or the
other.

## Playbook — first 60 seconds of a WCTF puzzle

The per-subgenre CTF prose in `knowledge/ctf/*.md` (23 files) is
authored and searchable via `search_lore`; the tool orchestration
below is what's live on the wire. When you land in an unfamiliar WCTF
room:

1. `pineapple_status()` — is the device reachable? Which transport
   answered? If SSH is down but API is up, transmit tools will fail
   later — flag it now.
2. `recon_start(band="both", dwell_ms=250)`, then `wait(s=15)`, then
   `recon_stop()`. Or one call: `run_sequence([
     {"action":"recon_start","band":"both","dwell_ms":250},
     {"action":"wait","s":15},
     {"action":"recon_stop"}])`.
3. `list_aps(seen_since_s=20)` — sort by security. Reach order:
   - **`open`** — no attack needed; just associate. Usually a trap
     (evil twin / captive portal). Diff against a known-good AP with
     `beacon_diff` before you trust it.
   - **`wpa2-psk` with PMKID in the beacon** — fastest lane. Go
     straight to `capture_pmkid(bssid=…)` → `convert_to_hashcat(mode=22000)`
     → `crack_start(wordlist_path="rockyou.txt")`. No client
     needed.
   - **`wpa2-psk` with a live client** — targeted deauth + capture:
     `capture_handshake(bssid=…, deauth_client=<mac>, timeout_s=60)`.
   - **`wpa3-sae` in transition mode** — RSN IE carries both
     AKM=2 (PSK) and AKM=8 (SAE). A WPA2-capable client can be
     kicked and its WPA2 side captured. The Dragonblood side-channel
     attacks are corpus material for later.
   - **`wpa3-sae` only, PMF-required** — offline crack is not on the
     table; look for a Dragonblood-style side channel, or pivot to
     the captive-portal / rogue-RADIUS side of the room.
   - **`wep`** — still real, still crack-in-under-a-minute-with-ARP-
     replay. If you see it in a WCTF, it's the puzzle.

Composing the crack pipeline as one call:

```python
run_sequence([
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 20},
    {"action": "recon_stop"},
    {"action": "capture_handshake",
     "bssid": "AA:BB:CC:DD:EE:FF", "timeout_s": 60,
     "deauth_client": "11:22:33:44:55:66"},
    {"action": "convert_to_hashcat",
     "pcap_path": "/tmp/handshake-AABBCCDDEEFF-01.pcap",
     "out_path":  "/tmp/handshake.22000"},
    {"action": "crack_start",
     "hash_path": "/tmp/handshake.22000",
     "wordlist_path": "rockyou.txt",
     "mode": 22000},
])
```

## Common WCTF patterns (tool-orchestration; corpus prose deferred)

- **PMKID fastpath.** `list_aps` shows AKM=2 (WPA2-PSK), then
  `capture_pmkid(bssid=…)` → check `extract_pmkids()` on the pcap →
  crack. Faster than a 4-way handshake because no client interaction.
- **Evil twin farm.** Multiple APs advertise the same SSID. `beacon_diff`
  (Phase 4+ when scapy is available) highlights the odd one out.
  Once identified, `evil_twin(target_bssid=…)` builds your own next to
  it — but for triage, the goal is usually to *find* the real one and
  associate with that.
- **Hidden SSID.** The SSID IE is null in beacons. `list_probe_requests`
  reveals it — a client that has *ever* seen the network volunteers
  the name on association. Wait, don't attack.
- **Captive-portal cred-flag.** `create_rogue_ap(security="open")`
  next to a target SSID, deauth clients off, serve a portal that
  templates the target's login page. The flag is what a user types.
- **Deauth against PMF.** Refuses. `respect_pmf=True` is the default;
  the refusal envelope cites the record so you can explain to a
  teammate why the shot didn't fire without a follow-up lookup.

## Diagnosing what happened

- `call_log` — every SSH command sent, verbatim, with exit codes and
  stderr. When `capture_handshake` returns ok=True but no handshake
  landed, the airodump/aireplay lines in `call_log` tell you whether
  the deauth actually went out.
- Every Pineapple-touching tool returns `{ok, transport, payload,
  timing_ms, warnings[]}`. `warnings[]` is where the interesting
  half-successes live — HTTP 5xx from the WebUI, non-zero exit codes
  from hcxdumptool, PMF-required refusals with citations.

## Legal & consent

Every tool that transmits (rogue AP, deauth, PineAP, beacon/probe
flood, packet inject) refuses to run unless
`--i-own-the-airspace` (per-session confirm flag) is set OR the
session's `authorization` config declares an explicit engagement
scope (SSID allowlist, MAC allowlist, time window, geo). At a DEF CON
WCTF you are on the village's sanctioned airspace and the flag is set
for the whole session; in an office lab you set the SSID allowlist.

Records for deauth and rogue-AP tools carry the appropriate legal
`caveat` field surfaced in the tool response envelope — same pattern
PHR34CKER5 uses for red-box / blue-box framing. Historical technique
is not a gate, but a caveat.

Every tool that transmits refuses if the airspace flag is missing;
the refusal cites `docs/legal_and_consent.md`.
