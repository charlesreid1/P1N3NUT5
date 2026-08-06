# PLAN — build the P1N3NUT5 knowledge base

> Status: **plan only, nothing authored yet.** Sibling to
> `plan-organize.md`; read that one first for the repo layout, transport
> split, and tool inventory. This file specifies the *contents* of
> `knowledge/`.

## Guiding rule — history is context, not the center

PHR34CKER5's corpus is history-heavy because most of the phone-phreaking
canon *stopped working* in the 90s and the whole game is about
recreating that era. Wireless is different. WEP is 25 years old, and
you still see it in industrial embedded gear; WPS is still on
consumer-grade routers in 2026; WPA2 4-way capture is still the primary
DEFCON WCTF workhorse. The wireless-security story is one of *layered
survival*, not *replaced era*.

So the corpus is organized around **modern techniques against modern
gear**, with historical technique carried in its own `history.md` files
per topic and in dated `era_bounds` on every record. A record for
"WEP FMS attack" carries `era_bounds: [1997, null]` (still effective
against any surviving WEP AP) and `still_effective_2026: true` — because
WEP APs are still deployed. A record for "TKIP MIC key recovery
(Beck-Tews)" carries `era_bounds: [2008, null]` but a note that TKIP
itself is nearly extinct on real infrastructure, so *the record exists,
it works, but it will rarely be reached for*. That distinction — is
this technique gone, or is the target rare — is a first-class field.

## Two-file design (mirrors PHR34CKER5)

- **`knowledge/<topic>/*.md`** — prose corpus. Human-readable, cited,
  organized by topic. What the assistant *reads*.
- **`knowledge/records/*.json`** — typed, dated, cited records. What
  the assistant *looks facts up in*. Numbers, not adjectives.

The prose corpus splits per-topic exactly the way PHR34CKER5 does:

```
knowledge/<topic>/
    README.md          Orient — what is this, why care. Short.
    reference.md       The technical spec — frame layouts, cipher
                       parameters, hashcat modes, exact fields.
                       Dry, complete, load-bearing.
    walkthrough.md     Worked examples. Real audio/traffic hints at
                       each step. Time-annotated. Failure modes.
    recognition.md     How to identify this thing on the air / in a
                       pcap. WCTF triage layer. "If the RSN IE says X
                       and the beacon rate is Y, you're looking at Z."
    history.md         Optional. The full story — landmark papers,
                       first-published exploits, timeline.
```

Not every topic needs all five files; use them as they earn their keep.
`fax/README.md` was PHR34CKER5's depth bar; here the bar is the
`wpa2/reference.md` + `wpa2/walkthrough.md` pair sketched below.

---

## The ontology

Categories the corpus MUST index (each maps to a `knowledge/<topic>/`
directory or a category tag on records):

- `standard` — 802.11 amendments (a/b/g/n/ac/ax/be/w/i/…), 802.1X,
  RFC 3748 (EAP), RFC 5216 (EAP-TLS), 802.11-2020 rollup
- `band_and_channel` — 2.4 GHz, 5 GHz (UNII-1/2A/2C/3/4), 6 GHz
  (UNII-5–8), channel numbers, widths (20/40/80/160/320), regulatory
  domains (US/EU/JP/…), DFS/TPC requirements
- `frame_type` — management (0), control (1), data (2), extension (3),
  subtypes, and where each appears in a session
- `information_element` — SSID, DS Parameter Set, TIM, Country, RSN,
  HT/VHT/HE/EHT Capabilities, WPS, Vendor-Specific, Extended Capabilities
- `cipher` — WEP, TKIP, CCMP-128, GCMP-128, GCMP-256, BIP-CMAC-128,
  BIP-GMAC-256
- `key_management` — Open, WEP, WPA-PSK/TKIP, WPA2-PSK/CCMP,
  WPA3-SAE, WPA3-SAE-H2E, WPA2/3-Enterprise (EAP methods), OWE
- `eap_method` — EAP-TLS, EAP-TTLS/PAP/CHAP/MSCHAPv2, PEAPv0/v1,
  LEAP, EAP-FAST, EAP-PWD, EAP-SIM/AKA/AKA'
- `attack` — every named attack: preconditions, tools, hashcat mode,
  mitigation, first-published, era_bounds, still_effective_2026,
  target_security[], transports_needed[]
- `cve` — CVE-indexed flaws (KRACK CVE-2017-13077…, Dragonblood
  CVE-2019-9494/9495, FragAttacks CVE-2020-24587…, WPS PIN CVE-2011-5053)
- `hashcat_mode` — mode number, capture format, source tool
- `pineapple_endpoint` — canonical Mark VII API + SSH capability records
  (see `plan-organize.md` transport section)
- `openwrt_uci` — UCI section names, options, defaults, side effects
- `defense_and_detection` — 802.11w PMF, MFP, WIDS/WIPS, rogue-AP
  detection heuristics, deauth-flood detection, evil-twin
  countermeasures, 802.1X authenticator hardening
- `bibliography` — canonical sources with pinpoint cites

The knowledge-retrieval MCP tools (`lookup_standard`, `lookup_frame`,
`lookup_ie`, `lookup_cipher`, `lookup_eap`, `lookup_attack`,
`lookup_cve`, `lookup_hashcat_mode`, `verify_claim`, `explain_attack`)
bind to these categories.

Every tool response carries the envelope `{citations[], era_bounds,
region, confidence ∈ {primary, secondary, community, folklore}}`.

---

## Prose topics — first-pass topic list

Modern-first. Order below is roughly the order the assistant will
reach for them at a WCTF.

### Tier 1 — modern workhorses (write first)

1. **`802.11/`** — how a modern WiFi session works end-to-end. Beacon
   → probe request/response → auth → assoc → 4-way handshake →
   data frames → disassoc. This is the frame the whole corpus hangs
   off. `reference.md` here is the 802.11-2020 rollup summary.

2. **`wpa2/`** — WPA2-PSK and WPA2-Enterprise. `reference.md`: 4-way
   handshake byte-by-byte (M1/M2/M3/M4), PMK derivation, PTK
   derivation, MIC. `walkthrough.md`: capture with airodump+deauth,
   convert with `hcxpcapngtool` to hashcat mode 22000, crack with
   rockyou. `recognition.md`: RSN IE fields, cipher suite selectors,
   PMF bit, distinguish PSK vs 802.1X in a beacon.

3. **`wpa3/`** — SAE (Dragonfly), H2E, transition mode, PMF-required.
   `reference.md`: SAE commit/confirm exchange, why offline crack
   doesn't apply the way it did in WPA2. `walkthrough.md`: how to
   attack — Dragonblood side channels, downgrade to WPA2 in transition
   mode, kick the client off the AP with disassoc, capture the retry.
   `recognition.md`: RSN IE difference (AKM 8 for SAE, 12 for OWE, 18
   for SAE-EXT-KEY), what a WPA2/WPA3 transition beacon looks like.

4. **`pmkid/`** — PMKID capture attack (Steube 2018). `reference.md`:
   the RSN IE PMKID field, why an AP hands it out unauthenticated,
   hashcat mode 22000 with only M1. `walkthrough.md`: `hcxdumptool`
   with the ESSID filter, convert, crack. `recognition.md`: which
   APs still leak PMKID in 2026 and which have started omitting it.

5. **`4-way-handshake/`** — deeper than `wpa2/` — a full topic on
   capturing, converting, and cracking 4-way handshakes across all
   the corner cases (M1+M2 only, M2+M3, PMF-protected disassoc,
   fast-transition 802.11r roams).

6. **`deauth/`** — the granddaddy of wireless attacks. `reference.md`:
   the 26-byte deauth frame, reason codes, how PMF/802.11w breaks it.
   `walkthrough.md`: targeted vs broadcast, `aireplay-ng -0` and
   `mdk4 d`. `recognition.md`: how a WIDS spots you.

7. **`evil-twin/`** — clone SSID+BSSID+channel, force reassociation.
   `reference.md`: the beacon-and-response fields that must match.
   `walkthrough.md`: `hostapd`+`hostapd-mana`, coupling with a captive
   portal. `recognition.md`: `beacon_diff` output to spot one.

8. **`pineap/`** — what the Mark VII's PineAP module actually does:
   beacon response, SSID pool broadcasting, karma, allow/deny filters.
   `reference.md`: the module architecture, config schema, filter
   semantics. `walkthrough.md`: sample engagement — enable karma,
   broadcast a pool of common home SSIDs, log probes for 15 minutes,
   generate a target list.

9. **`captive-portal/`** — the WCTF favorite. `reference.md`: DHCP →
   DNS → HTTP redirect → login form → optional credential-exfil.
   `walkthrough.md`: standing one up on the Pineapple, templating
   for the target vendor. `recognition.md`: signs a captive portal
   is a trap (cert-name mismatch, absent HSTS, weird DNS).

10. **`hashcat/`** — the crack side of the game. `reference.md`:
    mode 22000 (PMKID/EAPOL, all-in-one 2018+), 2500 (legacy WPA
    EAPOL), 5500 (NetNTLMv1), 16800/16801 (PMKID legacy),
    22001 (WPA*01 PMKID+EAPOL split). `walkthrough.md`: hashcat CLI
    ergonomics, rules, custom wordlists, `-w 4 --status`.

### Tier 2 — historical-but-alive (write next)

11. **`wep/`** — because it *still exists* in the wild.
    `reference.md`: RC4 keystream, IV length, ICV. `walkthrough.md`:
    aircrack-ng FMS/KoreK/PTW; ARP-request replay to accelerate.
    `recognition.md`: WEP-only APs in the beacon (no RSN IE, no
    WPA vendor IE, "Privacy" bit set).

12. **`wps/`** — PIN brute (Reaver, Pixie Dust). `reference.md`: the
    8-digit PIN structure (7+1 with checksum, split into two halves
    → 11k trials worst case). `walkthrough.md`: `reaver`, `bully`,
    `pixiewps` against APs that leak nonces (Broadcom/Ralink era).
    `recognition.md`: WPS IE in the beacon, WPS Locked bit.

13. **`krack/`** — Vanhoef 2017. `reference.md`: the KRACK family
    (CVE-2017-13077…-13088), which reinstall which key, what changes
    on Linux (all-zero PTK). `walkthrough.md`: mitm attack setup on
    a stack we know is vulnerable. `recognition.md`: whether a client
    is patched (rare in 2026, but not zero on embedded).

14. **`fragattacks/`** — Vanhoef 2020. `reference.md`: 12 CVEs,
    fragmentation cache, mixed-key attack. `walkthrough.md`: crafted
    frame sequences. `recognition.md`: patching status by vendor.

15. **`dragonblood/`** — Vanhoef+Ronen 2019, side-channel + timing
    against WPA3-SAE. `reference.md`: MODP-group selection oracle,
    Brainpool timing.

16. **`802.1x-eap/`** — enterprise WiFi. `reference.md`: 802.1X
    framing, EAPOL-Start, EAP-Request/Response/Success/Failure. Each
    EAP method as its own record. `walkthrough.md`: rogue RADIUS
    against PEAP-MSCHAPv2, asleap on the challenge-response.
    `recognition.md`: distinguishing PEAP/EAP-TTLS/EAP-TLS by
    outer-fragment behavior.

### Tier 3 — hardware / OpenWRT

17. **`pineapple-mk7/`** — the device itself. `reference.md`: hardware
    (dual radios, USB tether, 2.4/5GHz split, LEDs), stock firmware
    modules, storage, LEDs. `walkthrough.md`: fresh setup, key
    upload, factory reset from a wedged state. `recognition.md`: is
    my Pineapple in a good state? — a checklist.

18. **`openwrt/`** — the userland. `reference.md`: UCI, `hostapd`,
    `wpa_supplicant`, `iw`, `iwconfig` (legacy but present), `logread`,
    `procd`, the filesystem layout. `walkthrough.md`: common UCI
    recipes phreak-adjacent to WCTF work (dump current AP config,
    disable a running service, force channel).

19. **`hostapd/`** — the AP daemon. `reference.md`: config
    directives cross-referenced against security modes, driver quirks
    on mac80211/ath9k/ath10k. `walkthrough.md`: build a rogue AP
    with WPA2-Enterprise pointing at a mock RADIUS.

20. **`hcx-tools/`** — `hcxdumptool`, `hcxpcapngtool`, and how they
    supplanted the aircrack-ng workflow for handshake capture.
    `reference.md`: command surface, output formats, hashcat 22000
    integration. `walkthrough.md`: full pipeline from air to cracked.

### Tier 4 — perception & analysis

21. **`pcap/`** — how we read a capture. `reference.md`: pcap vs
    pcapng, radiotap headers, common filter recipes. `walkthrough.md`:
    tshark one-liners for AP enumeration, handshake completeness,
    probe-request profiling.

22. **`fingerprinting/`** — probe-request based device fingerprinting.
    `reference.md`: what varies (IE order, extended capabilities,
    supported rates), what fingerprint databases exist (Wireshark's
    IEEE OUI, hoover-style probe DBs). `walkthrough.md`: identifying
    an iPhone vs a Samsung TV vs a Raspberry Pi from probes alone.

23. **`ies/`** — Information Elements as a first-class topic. Every
    IE the assistant will ever see. Backed by `records/ies.json`.

### Tier 5 — CTF-facing (the P1N3NUT5 analog of PHR34CKER5's `ctf/`)

24. **`ctf/`** — one file per WCTF puzzle subgenre:
    - `hidden-ssid-mazes.md` — SSIDs revealed only in probe responses
    - `pmf-required-targets.md` — how to work around PMF (or not)
    - `wpa2-crack-flags.md` — the classic "PSK is the flag"
    - `wpa3-transition-downgrade.md` — PMK from the WPA2 side of a
      transition-mode AP
    - `evil-twin-farms.md` — a WCTF that gives you many APs and one
      is the trap
    - `captive-portal-cred-flags.md` — the flag is what a user types
    - `pmkid-fastpath.md` — a PMKID-leaking AP is often the fast lane
    - `beacon-flag-stego.md` — the flag is hidden in beacon IEs
    - `probe-request-flag.md` — a rogue client is leaking the flag in
      its preferred-network list
    - `deauth-forensics.md` — the flag is a specific reason code in a
      seen deauth frame
    - `rogue-radius-eap-flag.md` — the flag is a MSCHAPv2 password
    - `wps-pin-flag.md` — WPS is on, brute the PIN
    Each: what it looks like in the first 60 seconds on the recon
    display, how to probe it, which MCP tools to reach for, common
    flag-hiding patterns.

### Tier 6 — glossary and orientation

25. **`glossary/`** — SSID, BSSID, MAC randomization, RSSI, MCS, IE,
    KMP, PMK, PTK, GTK, PMKID, ANonce/SNonce, MIC, PN, EAPOL-Key,
    OWE, SAE, PMF, MFP, WIDS, hcxdumptool, aircrack-ng. Growing.

26. **`zines-and-talks/`** — the DEFCON/BSides/CCC talk canon:
    Cache 2001 WEP paper, Wright & Cache "Hacking Exposed Wireless",
    Wright's `asleap`, Vanhoef's whole run, Steube's PMKID advisory.
    `reference.md`: table of landmark talks with URLs, DOIs, GitHub
    repos. Pointers, not paraphrase.

---

## Records ontology — the JSON KR

Mirrors PHR34CKER5's `knowledge/records/` layout. Everything below is
`knowledge/records/<file>.json`, each a JSON array of records.

| file | category | what's in it |
|---|---|---|
| `standards.json` | `standard` | 802.11 amendments + related IETF/IEEE specs |
| `channels.json` | `band_and_channel` | every 2.4/5/6 GHz channel: number, center MHz, width options, regulatory status per region, DFS/TPC required |
| `frame_types.json` | `frame_type` | management/control/data/extension types and subtypes, byte offsets, field layout |
| `ies.json` | `information_element` | every IE the assistant will encounter, with byte layout |
| `security_suites.json` | `cipher` + `key_management` | RSN cipher suite selectors, AKM selectors, key derivation |
| `eap_methods.json` | `eap_method` | inner/outer, cred type, replay properties, known attacks |
| `attacks.json` | `attack` | full attack catalog — preconditions, tools, hashcat mode, mitigation, era_bounds |
| `cves.json` | `cve` | wireless CVEs cross-referenced from `attacks.json` |
| `hashcat_modes.json` | `hashcat_mode` | mode number, format, producer tool, example |
| `pineapple_endpoints.json` | `pineapple_endpoint` | every API path + SSH command the MCP invokes |
| `openwrt_uci.json` | `openwrt_uci` | UCI section catalog for `network`, `wireless`, `dhcp`, `firewall`, `hostapd`, `pineap` |
| `defense_and_detection.json` | `defense_and_detection` | PMF, WIDS behaviors, deauth-flood detection, evil-twin detection |
| `bibliography.json` | `bibliography` | pinpoint sources — IEEE, RFC, DEFCON, USENIX, GitHub, vendor docs |

### Record shape (mirrors PHR34CKER5)

```json
{
  "id": "kebab-case-unique",
  "name": "human name",
  "aliases": ["other names"],
  "category": "attack | cipher | eap_method | ...",
  "region": "universal | US | EU | JP | ...",
  "era_bounds": ["2018-08-04", null],
  "still_effective_2026": true,
  "confidence": "primary | secondary | community | folklore",
  "citations": ["bib-id", "..."],
  "see_also": ["other-record-id"],
  "disputed": { "field": "why disputed + competing values" },
  "technical_body": { ... },
  "preconditions": [ ... ],
  "tools": ["hcxdumptool", "hashcat"],
  "transport": "ssh | api | analysis"
}
```

- `era_bounds` is `[first_effective, last_effective]`; either end may be
  `null`. `explain_attack` refuses when caller-specified era lies
  outside the bounds — but returns steps by default (WCTF ethos).
- `still_effective_2026` distinguishes techniques that are gone from
  techniques whose *targets* are gone but whose *technique* still works
  where the target survives.
- `citations` must be non-empty; every entry resolves to
  `bibliography.json`. Loader raises on violation.
- `confidence`: `primary` (IEEE/IETF/vendor spec) > `secondary`
  (DEFCON talk with released code, USENIX paper) > `community` (blog,
  GitHub README, con hallway) > `folklore` (unverified claim, tribal
  knowledge). Same weighting as PHR34CKER5.
- `disputed` is never silently resolved — surface both values with
  provenance and let `verify_claim` return `needs_qualification`.

### Sample records (illustrative, not exhaustive — actual JSON to be authored)

#### `attacks.json` — PMKID capture

```json
{
  "id": "pmkid-capture",
  "name": "PMKID capture attack",
  "aliases": ["Steube PMKID", "M1-only WPA attack"],
  "category": "attack",
  "region": "universal",
  "era_bounds": ["2018-08-04", null],
  "still_effective_2026": true,
  "confidence": "primary",
  "citations": ["steube-2018-pmkid-hashcat-forum", "hashcat-mode-22000"],
  "preconditions": [
    "target uses WPA2-PSK or WPA3-transition WPA2 side",
    "target AP includes PMKID in first EAPOL message",
    "no client association required"
  ],
  "tools": ["hcxdumptool", "hcxpcapngtool", "hashcat"],
  "transport": "ssh",
  "hashcat_mode": 22000,
  "capture_format": "hccapx-superseded → 22000 hash line",
  "mitigation": [
    "AP firmware omits PMKID from M1",
    "WPA3-SAE only (no transition)",
    "strong PSK (long, high-entropy)"
  ],
  "target_security": ["wpa2-psk"],
  "see_also": ["wpa2-4-way-handshake", "hashcat-mode-22000"],
  "notes": "Faster than 4-way handshake capture because no client interaction is needed. Vendor adoption of the mitigation has been uneven; many consumer APs in 2026 still leak PMKID."
}
```

#### `security_suites.json` — WPA3-SAE

```json
{
  "id": "wpa3-sae",
  "name": "WPA3-SAE (Simultaneous Authentication of Equals)",
  "aliases": ["Dragonfly", "SAE"],
  "category": "key_management",
  "region": "universal",
  "era_bounds": ["2018-06-25", null],
  "confidence": "primary",
  "citations": ["rfc7664", "ieee-802-11-2020", "wifi-alliance-wpa3-spec"],
  "technical_body": {
    "akm_selector": "00-0F-AC:8 (SAE), 00-0F-AC:24 (SAE-EXT-KEY)",
    "requires_pmf": true,
    "kdf": "HMAC-SHA-256 (SAE), HMAC-SHA-384 (SAE-EXT-KEY)",
    "curves_default": "P-256",
    "curves_allowed": ["P-256", "P-384", "P-521", "MODP-groups (deprecated)"],
    "commit_exchange": "Peer-Commit-Element + scalar",
    "confirm_exchange": "MIC over confirm elements",
    "pmk_bytes": 32,
    "offline_dictionary_resistance": "high, absent side channel"
  },
  "disputed": {
    "offline_dictionary_resistance": "Dragonblood (Vanhoef+Ronen 2019, CVE-2019-9494/9495) demonstrates side-channel + timing attacks that partially defeat the resistance property when weak MODP groups are used. Records for those CVEs are in cves.json."
  },
  "see_also": ["dragonblood", "wpa3-transition-mode", "pmf"]
}
```

#### `pineapple_endpoints.json` — list_aps

```json
{
  "id": "list-aps",
  "capability": "enumerate access points seen by recon",
  "transports": ["api", "ssh"],
  "primary": "api",
  "api": {
    "method": "GET",
    "path": "/api/recon/ap",
    "auth_scope": "recon.read",
    "response_shape": "array of {bssid, ssid, channel, rssi, security, last_seen, ies?}"
  },
  "ssh": {
    "cmd": "iw dev wlan1 scan | awk -f /root/parse_scan.awk",
    "requires_root": true,
    "requires_monitor": false,
    "fallback_for": "when recon service is disabled or the WebUI backend is unresponsive",
    "warning": "SSH path returns only the current-moment scan, not the accumulated recon DB"
  },
  "firmware_min": "3.0.0",
  "firmware_max": null,
  "notes": "Prefer API. SSH path is real-time-only; the WebUI's cached DB has more history."
}
```

---

## Explicitly disputed / ambiguous entries the corpus must flag

The wireless-security literature is less contradictory than phreaking's
because most of it is published, dated, and code-backed. But there are
still traps:

- **"PMF prevents deauth."** Partial. PMF makes broadcast deauth/disassoc
  ineffective; unicast deauth toward a PMF-capable client is
  authenticated. But PMF-disabled clients on a PMF-capable AP can still
  be deauthed (transition mode); some drivers silently drop malformed
  deauths anyway. Record: `verify_claim("PMF stops deauth") →
  needs_qualification`.
- **"WPA3 fixes offline dictionary attack on the PSK."** Partial.
  Dragonblood (2019) demonstrated side channels. Also, WPA3 transition
  mode lets an attacker capture a WPA2 handshake and crack that. Record:
  `verify_claim("WPA3 defeats offline PSK cracking") →
  needs_qualification`.
- **"PMKID is always leaked."** No — vendor-dependent. Many recent
  firmwares omit PMKID from M1 by default. Records are per-vendor and
  dated.
- **"Client MAC randomization prevents tracking."** Partial. It defeats
  naive SSID+MAC correlation; probe-request IE fingerprinting still
  identifies a device. iOS since ~14 randomizes per-SSID; Android
  behavior varies. Records per-OS and dated.
- **"Broadcast SSID = insecure."** No — hidden SSIDs are recoverable
  from probe requests and offer no security. Record:
  `verify_claim("Hiding SSID improves security") → false`.
- **"WPS Pixie Dust works on every WPS AP."** No — vendor+chipset
  dependent (Broadcom, Ralink historically vulnerable; MediaTek
  variable). Record: enumerate vendor status.
- **"6 GHz devices can't be attacked with old tools."** True on the
  radio side (many 5 GHz-only tools) but the *protocols* (WPA3-only in
  6 GHz per Wi-Fi 6E rules) are attackable via Dragonblood-family
  techniques where applicable.
- **"You can always downgrade a WPA3 transition-mode AP to WPA2."**
  Only when a WPA2-capable client is willing to associate. Purely
  WPA3-only clients won't downgrade. Record: preconditions matter.
- **"Reaver still works."** Sometimes. Vendor lockout, WPS-Locked bit,
  and Wi-Fi Alliance's WPS deprecation guidance have thinned the
  target pool. Record: `still_effective_2026: true` with
  `target_availability: rare`.
- **"Deauth reason code 7 is 'class 3 frame from nonassociated STA'."**
  True in 802.11-2016 §9.4.1.7; some tutorials misquote. Record cites
  the standard.

---

## Bibliography discipline — pinpoint, not vibes

Non-exhaustive first-cut:

1. **IEEE 802.11-2020** — the rollup. §12 (security) is the load-bearing
   chapter. Cite by section number, not "the 802.11 standard."
2. **IEEE 802.11-2016** — the previous rollup; still cited for legacy
   behavior (WEP, TKIP, pre-SAE).
3. **IEEE 802.1X-2020** — port-based access control.
4. **RFC 3748** — EAP.
5. **RFC 5216** — EAP-TLS.
6. **RFC 5281** — EAP-TTLSv0.
7. **RFC 7664** — Dragonfly (SAE mathematical base).
8. **Wi-Fi Alliance WPA3 Specification** — the profile spec.
9. **Wi-Fi Alliance WPS Specification 2.0** — WPS.
10. **Fluhrer, Mantin, Shamir (2001)** — original WEP RC4 keystream
    attack (FMS). USENIX / Selected Areas in Cryptography.
11. **KoreK (2004)** — WEP attack refinement.
12. **Tews, Weinmann, Pyshkin (2007)** — PTW attack (aircrack-ng
    default).
13. **Beck, Tews (2008)** — TKIP MIC key recovery.
14. **Steube (2018)** — PMKID capture attack, hashcat forums.
15. **Vanhoef, Piessens (2017)** — KRACK, ACM CCS 2017.
16. **Vanhoef, Ronen (2019)** — Dragonblood, IEEE S&P 2020.
17. **Vanhoef (2020)** — FragAttacks, USENIX Security 2021.
18. **Bongard (2014)** — Pixie Dust (WPS offline attack), presented
    Passwords ^14.
19. **Cassola, Robertson, Kirda, Noubir (2013)** — rogue-AP detection.
20. **Wright, Cache** — "Hacking Exposed Wireless" (3rd ed.); Wright's
    `asleap`.
21. **Wi-Fi Alliance certification database** — verify vendor claims.
22. **hashcat documentation** — mode 22000 supersession of 2500/16800.
23. **hcxtools GitHub** — canonical `hcxdumptool` / `hcxpcapngtool`
    usage; supersedes aircrack-ng workflow.
24. **aircrack-ng documentation** — the still-canonical toolkit for
    legacy captures.
25. **Hak5 Pineapple Mark VII documentation** — the vendor's own docs
    for the API surface, module system, firmware release notes.
26. **OpenWRT UCI documentation** — canonical for `network`, `wireless`,
    `dhcp`, `firewall`, `hostapd` config.
27. **CVE Mitre entries** — CVE-2017-13077…-13088 (KRACK),
    CVE-2019-9494/9495 (Dragonblood), CVE-2020-24586…-24588
    (FragAttacks), CVE-2011-5053 (WPS PIN).

**Every `reference.md` file cites at least one primary source at the
bottom.** Same discipline as PHR34CKER5: no primary cite, no record
loads.

---

## Historical/legal framing (era-authentic references)

A short `knowledge/history/` or per-topic `history.md` block should
carry, at minimum:

- **2001 — Fluhrer/Mantin/Shamir WEP paper.** The moment WEP died.
- **2003 — Wi-Fi Alliance certifies WPA (interim).**
- **2004 — 802.11i ratified (WPA2, CCMP).**
- **2007 — Tews/Weinmann/Pyshkin PTW attack.** Practical WEP crack
  under a minute.
- **2008 — Beck/Tews TKIP MIC recovery.** TKIP starts its decline.
- **2011 — Viehböck WPS PIN attack.** Reaver released.
- **2014 — Bongard Pixie Dust.** WPS is done.
- **2017 — Vanhoef/Piessens KRACK.** Every WPA2 client patched over
  the next 24 months.
- **2018 — Steube PMKID.** Client-free WPA2-PSK capture.
- **2018 — Wi-Fi Alliance certifies WPA3.**
- **2019 — Vanhoef/Ronen Dragonblood.** WPA3-SAE gets a black eye.
- **2020 — 802.11ax (Wi-Fi 6) rollup.**
- **2020 — 6 GHz opened (US), Wi-Fi 6E.**
- **2021 — Vanhoef FragAttacks.** Twelve CVEs.
- **2024 — Wi-Fi 7 (802.11be) products ship.**

Every DEFCON WCTF talk sits in this timeline; every attack record
carries the paper year in `era_bounds`.

---

## Build/populate plan

1. **Schema.** JSON Schemas for each record type. Enforce `citations[]`
   non-empty and every entry resolves to `bibliography.json`. Enforce
   `era_bounds` as `[first_effective, last_effective]` with ISO dates
   or null.
2. **Seed data.** Hand-author the core records:
   - ~30 `standards.json` records (every 802.11 amendment through be,
     plus 802.1X, key EAP RFCs)
   - ~180 `channels.json` records (every US 2.4 + 5 + 6 GHz channel
     with regulatory status; per-region variants folded in)
   - ~40 `frame_types.json` records (every subtype + a note on where
     it appears)
   - ~60 `ies.json` records
   - ~30 `security_suites.json` records (RSN cipher suites, AKM
     suites, WEP variants)
   - ~25 `eap_methods.json` records
   - ~40 `attacks.json` records (Tier 1 + Tier 2 topics fully covered)
   - ~20 `cves.json` records (KRACK family, Dragonblood, FragAttacks,
     WPS PIN, PMKID mitigation flags)
   - ~30 `hashcat_modes.json` records (the WiFi-relevant subset)
   - ~50 `pineapple_endpoints.json` records (every API path + SSH
     command the MCP is going to call)
   - ~40 `openwrt_uci.json` records
   - ~25 `defense_and_detection.json` records
   No web-scrape auto-generation — every record hand-verified.
3. **Test corpus.** ~100 gold-standard Q/A pairs mined from DEFCON
   WCTF write-ups, Wright/Cache, Vanhoef's papers, and hashcat forum
   threads. The assistant + MCP must answer each correctly.
4. **Adversarial corpus.** ~40 trap questions where the "obvious"
   answer is wrong (PMF stops all deauth; WPA3 kills offline attack;
   hidden SSID is secret). `verify_claim` must return the right
   graded verdict.
5. **Era/vendor coverage matrix.** A test that samples the corpus by
   `(era, vendor)` cell and confirms non-empty coverage across the
   {WPA2-era, WPA3-era, Wi-Fi 6/6E-era} × {Cisco, Ubiquiti, TP-Link,
   MikroTik, Ruckus, consumer-mesh} matrix.
6. **Citation integrity.** CI check — every `citations[]` entry
   resolves to a `bibliography.json` id; no orphaned bib records.
7. **Fixture pcaps.** For every `frame_types.json` record and every
   `attacks.json` Tier-1 record, ship a small `.pcapng` fixture under
   `tests/fixtures/` so the perception tools have a deterministic
   parse target. Fixtures are keyed by record id.
8. **WCTF-readiness pass.** Dry-run against a panel of wireless-CTF
   veterans (past DEFCON Wireless Village authors). Their objections
   become bug reports. Non-negotiable if the goal is "battle-tested at
   DEFCON."

---

## Non-goals for the knowledge corpus

- **No client-side exploitation of arbitrary hosts.** Once we've
  cracked a PSK or dropped a client on the rogue AP, we stop. Post-
  exploitation is a separate discipline.
- **No cellular / LTE / 5G attacks.** Different physical layer,
  different tools, different repo.
- **No BLE / classic Bluetooth.** Same.
- **No zero-day work.** The corpus documents published attacks. New
  research belongs in an academic venue first, then in a record here
  once cited.
- **No production-only credentials.** Enterprise EAP defaults? Yes —
  educational, dated, cited. Any specific customer's radius secret? No.
- **No CVE payload weaponization beyond POC-scale.** Records point at
  published POCs; the corpus doesn't wrap or extend them.

---

## Acceptance criteria — how we know the corpus is ready

- 100% of `security_suites.json` records round-trip through schema
  validation with numeric-field completeness (AKM selector hex, cipher
  bit lengths, PMK bytes).
- 100% of `attacks.json` records have `preconditions`, `tools`,
  `mitigation`, `era_bounds`, `hashcat_mode` (or explicit null), and
  at least one primary or secondary citation.
- 100% of `pineapple_endpoints.json` records have both `firmware_min`
  and at least one of `api` or `ssh` populated.
- 100% of `channels.json` records have per-region regulatory status.
- 100% of ~100 test-corpus questions answered with exact agreement
  (not "roughly WPA3-ish").
- 100% of trap questions result in `verify_claim` returning `false` or
  `needs_qualification` with citations to the correct record.
- Zero records with empty `citations[]`.
- A written "known-unknowns" appendix — every claim we couldn't nail
  to a primary source is listed there.

---

## Appendix A — Quick reference cheat sheet

The corpus must be able to render this correctly on demand (belongs in
`knowledge/cheatsheet.md`):

- **2.4 GHz channels (US):** 1–11 usable, 20 MHz, non-overlapping 1/6/11.
- **5 GHz UNII-1:** ch 36–48, no DFS/TPC.
- **5 GHz UNII-2A/2C:** ch 52–64 / 100–144, DFS + TPC required.
- **5 GHz UNII-3:** ch 149–165, no DFS/TPC (US).
- **6 GHz (US, UNII-5–8):** ch 1–233, WPA3-only mandate (Wi-Fi 6E).
- **RSN AKM 2 = PSK; 8 = SAE; 12 = OWE; 18 = SAE-EXT-KEY.**
- **RSN cipher suite selector 4 = CCMP-128; 8 = GCMP-128; 9 = GCMP-256;
  6 = BIP-CMAC-128.**
- **Deauth reason 7 = "class 3 frame received from nonassociated STA."**
- **PMKID capture → hashcat mode 22000.**
- **4-way handshake (M1+M2 or better) → hashcat mode 22000
  (2018+) or legacy 2500.**
- **802.11w PMF: management-frame protection; blocks broadcast
  deauth/disassoc, protects unicast versions.**
- **WPA3 transition mode: RSN IE carries both AKM 2 (PSK) and AKM 8
  (SAE) — this is the downgrade opportunity.**
- **Pineapple Mark VII default gateway (USB-tether): 172.16.42.1.**
- **Pineapple Mark VII WebUI: HTTPS on 1471 (varies by firmware).**

---

## Appendix B — Sample `attacks.json` records (schema exemplars)

To be authored in Phase 2. See the WPA3-SAE and PMKID records earlier
in this document for the shape. Author at minimum:

- `wep-fms`, `wep-korek`, `wep-ptw`, `wep-arp-request-replay`
- `wpa2-4way-capture`, `pmkid-capture`, `pmk-crack-hashcat`
- `wps-reaver-online`, `wps-pixie-dust`, `wps-null-pin`
- `krack-client-key-reinstall`, `krack-ap-key-reinstall`
- `dragonblood-sidechannel`, `dragonblood-timing`,
  `wpa3-transition-downgrade`
- `deauth-broadcast`, `deauth-targeted`, `disassoc-targeted`
- `beacon-flood-mdk4`, `probe-flood-mdk4`, `authentication-flood`
- `evil-twin-clone`, `evil-twin-karma`, `evil-twin-known-beacons`
- `captive-portal-cred-capture`, `rogue-radius-mschapv2-capture`,
  `asleap-mschapv2-crack`
- `pineap-passive-probe-log`, `pineap-active-karma`
- `fragattacks-mixed-key`, `fragattacks-cache-poisoning`
- `frame-injection-arbitrary`

Each with preconditions, hashcat mode (or null), tool chain, era_bounds,
and citations.
