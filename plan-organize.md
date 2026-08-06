# PLAN — organize P1N3NUT5 for the DEF CON WiFi CTF

> Status: **plan only, nothing built yet.** Sibling to `plan-knowledge.md`;
> read the two together. This file lays out the repo, the MCP tool
> surface, and the API-vs-SSH split. `plan-knowledge.md` lays out the
> knowledge base.

## What we're building

**P1N3NUT5** is the wireless-CTF twin of PHR34CKER5. A single MCP server
that (a) knows 802.11 — standards, frames, ciphers, attacks, tools, the
whole modern-and-historical WiFi security stack — and (b) actually drives
a **Hak5 WiFi Pineapple Mark VII** end-to-end so an assistant can
compose scripted engagements ("scan 5 GHz for 20s, pick the AP with the
weakest security, capture its 4-way handshake, convert to hashcat 22000,
kick off a dictionary run") without a human in the loop for every step.

Three tiers, from knowing to acting to perceiving:

- **Know** — corpus + typed records (802.11 standards, frame layouts,
  attack catalog, CVE-annotated flaws, Pineapple hardware & API surface).
- **Act** — control the Pineapple: recon, PineAP, rogue AP, evil twin,
  deauth, capture, injection. Two transports (see below).
- **Perceive** — parse pcaps, extract handshakes/PMKIDs, decode IEs, feed
  captures into hashcat and read back status.

## Where PHR34CKER5 ends and P1N3NUT5 begins

Same architecture, different center of gravity:

| axis | PHR34CKER5 | P1N3NUT5 |
|---|---|---|
| era focus | history-heavy (1965–2003) | **modern-heavy** (WPA2/WPA3 workhorses); history is context, not the target |
| action transport | one (Twilio REST + Media Streams) | **two** (Pineapple REST API + SSH) |
| corpus discipline | dated, cited, region-bound, disputed-aware | same discipline; more of the corpus is "current gear" |
| primary artifact | a WAV or a live PSTN call | a pcap, a captured handshake, a rogue AP, a cracked PSK |
| KR emphasis | tone tables & signaling systems | **frame layouts, cipher suites, attack preconditions, hashcat modes** |

The historical layer matters — WEP, WPS, KRACK, Dragonblood, FragAttacks
are all landmark parts of the domain and canonical DEFCON WCTF material —
but unlike phreaking, the *current-era* toolkit (WPA2 4-way, PMKID,
evil-twin captive portals, PMF-aware deauth) is where the assistant
spends most of its time. Records that describe a 2001 WEP break carry
`era_bounds` like everything else; records for the 2026 workhorse
techniques dominate the corpus.

---

## Repo map (mirrors PHR34CKER5)

```
src/p1n3nut5_mcp/          the MCP server (installable Python package)
    __main__.py            entry point
    server.py              MCP tool declarations
    pineapple_api.py       REST client to the Pineapple (auth, endpoints)
    pineapple_ssh.py       SSH command executor (paramiko or asyncssh)
    pineapple_transport.py picks API-or-SSH per capability
    recon.py               parse/enrich recon DB responses
    records.py             typed record loader (mirrors PHR34CKER5)
    detect.py              pcap parsing, handshake extraction
    attacks.py             composed attack sequences
    hashcat.py             thin wrapper around a local hashcat
    runtime.py             config, credential resolution, session state
knowledge/                 prose corpus (one topic per dir) + records/
    MANIFEST.md
    <topic>/README.md, reference.md, walkthrough.md, recognition.md
    records/*.json         typed, cited, dated — see plan-knowledge.md
skills/pineapple/          SKILL.md that teaches an assistant to use the MCP
scripts/                   user-facing shell helpers (creds, key setup, fixtures)
docs/                      long-form guides (pineapple_setup, wctf_playbook, ...)
tests/                     pytest suite (parsers + fake-transport; no live radio)
```

Everything not listed above is deliberately absent. In particular, no
top-level Python modules outside `src/`, no bundled binaries, no captured
pcaps — fixtures live under `tests/fixtures/` and are small and named.

`scripts/` and `src/` stay separate for the same reason PHR34CKER5 keeps
them apart: `scripts/` is what a human runs once at setup (`setup-pineapple.sh`,
`fetch-firmware-manifest.py`), `src/` is what runs every time the MCP
answers a tool call.

---

## The transport split — API vs SSH

The Pineapple Mark VII exposes two control surfaces. Some jobs work
cleanly on one, some only on the other, some on both. The MCP wraps
both and hides the choice behind each tool — but the choice is
principled, not arbitrary, and the record for each MCP tool (in
`records/pineapple_endpoints.json`) declares which transport it uses and
why.

### REST API (`https://<pineapple>/api/…` with a bearer token)

The web UI's own backend. Stable JSON, structured errors, per-endpoint
auth scope.

**Best for:**
- Dashboard / status / uptime / firmware version
- Recon control (start/stop scans, dwell time, band selection)
- Recon data pull (AP list, client list, probe requests, associations)
- PineAP config (SSID pool, karma/allow-associations toggles, filter
  lists — allow/deny SSIDs, allow/deny clients)
- Module management (install/enable/disable/uninstall)
- Filter and log management via structured endpoints
- Anything the WebUI does — because that IS how the WebUI does it

**Limits:**
- Rate-limited on some paths; not intended for high-frequency polling
- Doesn't expose raw packet capture, injection scripts, or arbitrary
  binaries — that's not what a REST surface is
- Payload shapes drift across firmware revisions; each record pins the
  minimum firmware it was verified against

### SSH (root@<pineapple>, key- or password-auth)

The underlying OpenWRT userland. `iw`, `iwconfig`, `hostapd`,
`wpa_supplicant`, `airmon-ng` / `aireplay-ng` / `airodump-ng`,
`hcxdumptool`, `hcxpcapngtool`, `tcpdump`, `mdk4`, `bettercap`, `kismet`,
`hostapd-mana`, plus every UCI knob (`uci show`, `uci set`, `uci commit`).

**Best for:**
- Raw frame capture (`tcpdump -i wlanXmon -w …`)
- Frame injection (`aireplay-ng`, `mdk4`, raw scapy over an SSH pipe)
- 4-way handshake capture via airodump + deauth pair
- PMKID capture (`hcxdumptool`)
- Manual `hostapd` for rogue APs with exotic parameters (WPA2-Enterprise
  rogue RADIUS, WPA3 SAE transition, unusual channel widths)
- File transfer for pcaps (`scp` under the SSH channel)
- Log tailing (`logread -f`, `tail -f /tmp/…`)
- Kernel/mac80211 tuning that has no API surface
- One-off shell recipes cited from `knowledge/` walkthroughs
- Custom `iw dev` incantations, monitor-mode setup on unusual chips

**Limits:**
- Ships live root shell → destructive if a tool is buggy. Every SSH
  tool records its shell invocation in `call_log` so post-mortems are
  possible.
- Command-shape assumptions can drift between firmware. Records pin
  known-good invocations to firmware versions.
- Some CTF venues may block outbound SSH from the Pineapple; use the
  onboard "Mark VII → laptop" wired path.

### The decision rule

For every capability we expose:

1. If the WebUI does it and shape is stable across firmwares → **API**.
2. If it's raw-radio, needs a subprocess, or touches files → **SSH**.
3. If both work, prefer API for observability and rate limiting, prefer
   SSH for low-latency loops (channel hop, packet inject) and when we
   need to `tail -f` a running process.
4. If a capability *only* exists on one transport, mark it so and don't
   pretend the other is a fallback. `deauth`, `capture_handshake`, and
   `capture_pmkid` are SSH-only. `list_modules`, `pineap_config`, and
   `dashboard` are API-only. `list_aps` is API-preferred with an SSH
   `iw dev wlanX scan` fallback for when the recon service is off.

Each `pineapple_endpoints` record carries:

```json
{
  "id": "kebab-case",
  "capability": "list_aps",
  "transports": ["api", "ssh"],
  "primary": "api",
  "api": {"method": "GET", "path": "/api/recon/ap", "auth_scope": "recon.read"},
  "ssh": {"cmd": "iw dev wlan0 scan | ...", "requires_root": true, "requires_monitor": false},
  "firmware_min": "3.0.0",
  "firmware_max": null,
  "notes": "..."
}
```

---

## MCP tool inventory

Organized by tier. Names are provisional but the shape is fixed. Every
tool that touches the Pineapple takes an implicit `pineapple` handle
(from env / config) and returns a stable structured envelope
`{ok, transport, payload, timing_ms, warnings[]}`.

### Know — corpus (read-only)

Parity with PHR34CKER5:

- `list_topics()` — every topic and file in the corpus
- `read_lore(topic, name)` — one file's contents
- `search_lore(query, max_results=20)` — case-insensitive regex/substring
- `random_lore()` — one random file

Every markdown file is also exposed as MCP resource
`p1n3nut5://<topic>/<name>`, plus `p1n3nut5://index`.

### Know — typed records (numbers, not adjectives)

The KR layer. Backed by `knowledge/records/*.json`. See
`plan-knowledge.md` for the record schemas.

- `lookup_standard(name)` — 802.11 variant spec (a/b/g/n/ac/ax/be):
  bands, max PHY rate, max channel width, MIMO streams, MCS, launch year
- `lookup_channel(number, band)` — center freq, width options, regulatory
  status per region (US/EU/JP), DFS/TPC required
- `lookup_frame(type, subtype)` — 802.11 frame layout, fields, length,
  when it appears on the air
- `lookup_ie(id_or_name)` — Information Element structure (SSID, RSN,
  HT/VHT/HE Capabilities, Vendor-Specific, WPS, etc.)
- `lookup_cipher(name)` — WEP/TKIP/CCMP/GCMP; block size, key size,
  IV/nonce structure, integrity method
- `lookup_eap(method)` — EAP method: transport, credential type, known
  flaws (LEAP dictionary, PEAP-MSCHAPv2 relay, EAP-PWD Dragonblood)
- `lookup_attack(name)` — full attack record: preconditions, tools,
  hashcat mode, mitigation, first-published date, era_bounds
- `lookup_cve(id)` — KRACK, Dragonblood, FragAttacks, and friends
- `lookup_hashcat_mode(name_or_number)` — mode number, capture format,
  producer tool, example command
- `verify_claim(text)` — grades claims `true / false /
  needs_qualification / unverified` against the trap catalog (e.g.
  "PMF prevents all deauth" → **needs_qualification**; "WPA3 fixes
  offline dictionary attack" → **needs_qualification** because of
  Dragonblood)
- `explain_attack(name, target_security?, era?)` — always returns the
  steps (the point at a WCTF is to *do* the attack). `target_security`
  and `era` add non-blocking context, never refusal.
- `bibliography(cite_id?)` — resolve a source id or list all
- `cross_reference(record_id)` — traverse `see_also`
- `search_records(query?, category?, era?, transport?)` — filter the KR

Every KR response carries `{citations[], era_bounds, region, confidence
∈ {primary, secondary, community, folklore}}`.

### Act — Pineapple recon (API-preferred)

- `pineapple_status()` — reachable? firmware? uptime? radios present?
- `list_interfaces()` — wlanX name, MAC, mode (managed/monitor/AP), band
- `recon_start(band=2.4|5|both, dwell_ms=…, hop_pattern?)`
- `recon_stop()`
- `recon_status()`
- `list_aps(seen_since_s?, ssid_regex?, band?, security?)` — cached
  recon list with structured filter args
- `list_clients(ap_bssid?, seen_since_s?)`
- `list_probe_requests(client_mac?, since_s?)`
- `list_associations(bssid?, client_mac?)` — associate/disassociate
  events
- `client_history(client_mac)` — trajectory + preferred networks
- `get_ap_details(bssid)` — full IE dump: cipher, KMP, PMF, vendor,
  WPS state
- `recon_download(path?)` — pull the recon DB as a file

### Act — PineAP (API)

- `pineap_status()` / `pineap_start()` / `pineap_stop()`
- `pineap_config({ssid_pool[], karma?, log_probes?, log_associations?,
  beacon_response?, broadcast_ssid_pool?, source_mac?, target_mac?, ...})`
- `pineap_beacon_add(ssids[])` / `pineap_beacon_remove(ssids[])`
- `pineap_beacon_pool_list()`
- `filter_ssid_list(mode='allow'|'deny')` /
  `filter_ssid_set(mode, ssids[])`
- `filter_client_list(mode)` / `filter_client_set(mode, macs[])`

### Act — rogue AP & captive portal (SSH-driven hostapd)

- `create_rogue_ap({ssid, bssid?, channel, band, security='open'|
  'wpa2_psk'|'wpa2_eap'|'wpa3_sae', psk?, radius?, hidden?, iface?})` —
  templated `hostapd.conf`, SCP'd to Pineapple, launched under a named
  process
- `list_rogue_aps()` — every rogue AP this MCP instance has running
- `stop_rogue_ap(handle)`
- `evil_twin(target_bssid, options?)` — clone SSID+BSSID+channel of a
  seen AP; optionally deauth clients off the real one to force
  reassociation
- `serve_captive_portal(handle, template='basic'|'vendor', backend?)` —
  bring up a captive portal in front of the rogue AP; the WCTF flag is
  often the credential a user types in
- `rogue_radius({user_realm?, response_policy='accept'|'challenge'})` —
  spin up a mock RADIUS to capture EAP-MSCHAPv2 challenge/response
  pairs for asleap

### Act — attack primitives (SSH)

- `deauth({bssid, client_mac?, count=5, reason=7, iface, respect_pmf=true})`
  — sends deauth frames; refuses cleanly (with a citation to the record
  and a note about PMF/802.11w) when the target advertises PMF-required
- `capture_handshake({bssid, timeout_s=60, out_path?, deauth_client?})`
  — starts airodump + optional targeted deauth; returns pcap path
- `capture_pmkid({bssid?, timeout_s=60, out_path?})` — hcxdumptool
  filter list mode
- `beacon_flood({ssid_list[], band, count?, iface?})` — mdk4 mode b
- `probe_flood(...)` — mdk4 mode p
- `packet_inject({iface, hex_or_pcap})` — raw frame injection
- `channel_hop_start(iface, pattern)` / `channel_hop_stop(iface)`
- `client_disassoc({bssid, client_mac, count=1})` — targeted assoc
  drop

### Perceive — capture analysis

Local (in the MCP host) so we can run offline against a downloaded pcap:

- `parse_pcap(path)` — frame-type histogram, unique BSSIDs/SSIDs/clients
- `extract_handshakes(pcap_path)` — EAPOL 4-way (M1/M2/M3/M4), returns
  which messages are present and how many complete
- `extract_pmkids(pcap_path)`
- `convert_to_hashcat(pcap_path, mode=22000|2500, out_path?)` — wraps
  `hcxpcapngtool`
- `crack_start({hash_path, wordlist_path?, rules_path?, mode})` — kicks
  off local hashcat, returns job id
- `crack_status(job_id)` / `crack_result(job_id)` / `crack_stop(job_id)`
- `decode_ies(bssid_or_pcap)` — human-readable IE breakdown
- `beacon_diff(bssid_a, bssid_b)` — highlight IE differences (useful
  for spotting an evil twin)
- `client_fingerprint(client_mac)` — best-effort vendor + OS guess from
  probe request IEs, seq numbers, timing (basic; deep fingerprinting is
  out-of-scope)

### Orchestrate — one atomic scripted engagement

`run_sequence(steps)` — the WiFi analog of `play_sequence`. Actions:

- Recon: `recon_start`, `recon_stop`, `wait_for_client`, `wait_for_ap`,
  `wait_for_probe`
- PineAP: `pineap_start`, `pineap_stop`, `pineap_config`
- Rogue: `create_rogue_ap`, `evil_twin`, `serve_captive_portal`,
  `stop_rogue_ap`
- Attack: `deauth`, `capture_handshake`, `capture_pmkid`,
  `beacon_flood`, `packet_inject`, `client_disassoc`
- Perceive: `parse_pcap`, `extract_handshakes`, `convert_to_hashcat`,
  `crack_start`, `crack_status`, `crack_result`
- Control: `wait`, `wait_until`, `assert`

Example — one call that captures a handshake and starts a crack:

```
run_sequence([
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 20},
    {"action": "recon_stop"},
    {"action": "capture_handshake", "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 60, "deauth_client": "11:22:33:44:55:66"},
    {"action": "convert_to_hashcat", "mode": 22000},
    {"action": "crack_start", "wordlist_path": "/opt/wordlists/rockyou.txt"},
])
```

### Support — operational polish

- `MAX_ROGUE_MINUTES` env cost/safety guardrail — auto-tear-down of any
  rogue AP running past the limit
- `call_log(session_id)` — full timeline of API + SSH commands, with
  timing, transport used, and warnings
- Structured events resource `p1n3nut5://sessions/<id>/events` so an
  assistant can subscribe instead of polling

---

## Env vars

| var | required | notes |
|---|---|---|
| `PINEAPPLE_HOST` | yes | `172.16.42.1` (default USB-tether) or a routable IP |
| `PINEAPPLE_TOKEN` | API | bearer token from the WebUI's admin page |
| `PINEAPPLE_SSH_USER` | SSH | usually `root` |
| `PINEAPPLE_SSH_KEY` | one of | path to private key |
| `PINEAPPLE_SSH_PASSWORD` | one of | fallback password auth |
| `PINEAPPLE_SSH_PORT` | no | default 22 |
| `PINEAPPLE_TRANSPORT_PREF` | no | `api` or `ssh` — override the default rule |
| `MAX_ROGUE_MINUTES` | no | auto-teardown of rogue APs. 0/unset disables. |
| `P1N3NUT5_KNOWLEDGE` | no | override corpus path (dev) |
| `HASHCAT_PATH` | no | path to hashcat if not on `$PATH` |
| `WORDLIST_DIR` | no | default lookup path for `crack_start` wordlists |

---

## Deployment topologies

**A. Laptop-tethered (standard con setup).** Pineapple over USB
Ethernet at `172.16.42.1`. MCP runs on the laptop. Assistant runs on
the laptop. Fast, private, no cloud.

**B. Bench / lab.** Pineapple on a lab LAN. MCP runs on a workstation.
Same shape, higher latency, more logging.

**C. Sync Cloud.** Hak5 offers a cloud dashboard; out of scope for the
MCP's first cut. The MCP talks directly to the device.

---

## Legal & consent

Wireless testing is more permissive than telephony but not free. Every
tool that transmits (rogue AP, deauth, PineAP, beacon/probe flood,
packet inject) refuses to run unless `--i-own-the-airspace` (a
per-session confirm flag) is set, OR the session's `authorization`
config declares an explicit engagement scope (SSID allowlist, MAC
allowlist, time window, geo). At a DEF CON WCTF you're on the village's
sanctioned airspace and the flag is set for the whole session; in an
office lab you set the SSID allowlist.

Records for deauth and rogue-AP tools carry the appropriate legal
`caveat` field surfaced in the tool response envelope. This is the same
pattern PHR34CKER5 uses for red-box/blue-box legal framing — historical
technique is not a gate, but a caveat.

---

## Suggested execution order

1. **Phase 0 — Repo skeleton (this file's target).** `pyproject.toml`,
   `src/p1n3nut5_mcp/{__init__,__main__,server,runtime}.py` empty stubs,
   `knowledge/MANIFEST.md`, `skills/pineapple/SKILL.md` skeleton, this
   `plan-organize.md` + `plan-knowledge.md`, `README.md` orientation.

2. **Phase 1 — Transport layer.** `pineapple_api.py` and
   `pineapple_ssh.py`, both against a fake fixture, then against a real
   Mark VII. `pineapple_status()` end-to-end on both transports proves
   the plumbing.

3. **Phase 2 — Knowledge base seed.** Author the ~40 core prose files
   and the seven top-priority JSON record files
   (`standards.json`, `channels.json`, `frame_types.json`,
   `security_suites.json`, `attacks.json`, `pineapple_endpoints.json`,
   `hashcat_modes.json`). See `plan-knowledge.md`. Same discipline as
   PHR34CKER5 — every record dated, cited, region-bound, disputed-aware.

4. **Phase 3 — Recon + PineAP tools.** `list_aps`, `list_clients`,
   `list_probe_requests`, `pineap_config`, `filter_*`. All API. This
   layer is what an assistant reaches for in the first 60 seconds of a
   WCTF puzzle.

5. **Phase 4 — Perceive tools.** `parse_pcap`, `extract_handshakes`,
   `convert_to_hashcat`, `crack_start`. Local, no radio; testable in
   CI against fixture pcaps. The Pineapple's role here is just to
   supply the pcap.

6. **Phase 5 — Attack primitives.** `deauth`, `capture_handshake`,
   `capture_pmkid`, `create_rogue_ap`, `evil_twin`. SSH-heavy. Every
   tool records its exact shell invocation.

7. **Phase 6 — Knowledge-retrieval tools.** `lookup_*`, `explain_attack`,
   `verify_claim`, `search_records`. Backed by the records shipped in
   Phase 2.

8. **Phase 7 — Orchestrate + polish.** `run_sequence`, `call_log`,
   events resource, cost guardrail, the SKILL playbook section.

9. **Phase 8 — Skill.** `skills/pineapple/SKILL.md` full first draft
   with WCTF playbook, corpus depth cues, and the API-vs-SSH note.

Each phase leaves the repo in a coherent state; stopping between phases
is fine. Phase 2 is the load-bearing one for "does it *sound* like it
knows what it's talking about," Phase 5 is the load-bearing one for
"does it *do* things."

---

## Non-goals for v1

- **No wireless-driver dev.** We don't ship a mac80211 patch; the
  Pineapple's stock firmware is the target.
- **No cellular.** LTE/5G sniffing, IMSI catchers, Osmocom, and their
  ilk are a separate repo. AMPS/GSM handset trivia lives in PHR34CKER5
  where it belongs to that era.
- **No Bluetooth / BLE.** Same reason. Related, distinct discipline.
- **No SDR beyond WiFi bands.** HackRF / RTL-SDR broad-spectrum work
  belongs elsewhere.
- **No offensive services beyond the airspace.** Once we've dropped a
  client onto our rogue AP and cracked a PSK, we hand off — the flag
  is either the credential itself or something the client did on the
  network we captured. Post-exploitation is out of scope.
