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

The corpus also weights toward the **frontier** — 2020–2024 research
(Kr00k, SSID Confusion, Framing Frames, MacStealer, Dragonblood follow-
ups, FT-handshake capture, 11r/11k/11v abuse, MC-MitM, Wi-Fi 6/6E
OFDMA/TWT surface, Wi-Fi 7 MLO). At DEF CON WCTF the puzzles push past
the "old hits" (WEP crack, plain PMKID, `aireplay -0` broadcast deauth)
that every 2014 writeup covers. Old hits stay in the corpus for
completeness, but frontier records have equal or greater weight, dated
citations to the original paper, and worked walkthroughs where the
research code is public.

## Scope rule — the airspace ends at the DHCP lease

The corpus's outer boundary is the **RF and 802.11 layer**, extending
just barely into L3 where a wireless attack's *natural next frame* takes
it — decrypting captured traffic with a recovered PSK, becoming a
legitimate STA once you own the key, spoofing the DHCP/DNS/gateway from
the rogue-AP side because the rogue AP *is* those services. Past that,
we hand off.

**In scope (RF and near-L3):**

- Everything that touches the air (management, control, data frames;
  ciphers; key management; roaming).
- Passive traffic decryption with a recovered PSK (Wireshark
  `wlan.enable_decryption`, per-session PTK derivation) — because this
  is how you *read* what you captured.
- Rogue-AP-side services (DHCP, DNS, HTTP redirect, captive portal,
  RADIUS) — because these run *on* the Pineapple and are part of the
  attack primitive.
- Becoming a legitimate STA with a cracked PSK — `wpa_supplicant` /
  `iwd` invocation from the Pineapple; this is the last-mile validation
  that the crack worked.
- Reading credentials or tokens the client hands to the rogue AP as
  part of the association / captive-portal / EAP exchange.

**Out of scope (LAN and beyond):**

- Lateral movement across the LAN, SMB/AD enumeration, Kerberoasting,
  Responder-style LLMNR/NBNS poisoning, mitm6, service scans.
- AP admin-plane exploitation (default-cred tables, RouterSploit, web
  UI CVEs). If a WCTF puzzle demands this, treat as out-of-band and
  reach for a general pentest toolkit outside P1N3NUT5.
- Post-crack RCE, C2, exfil, arbitrary-host exploitation.
- Cellular, BLE, Zigbee, LoRa, HackRF broad-spectrum.

The reason for the sharp line: DEF CON's wireless CTF traditionally puts
flags in RF-side artifacts (the PSK itself, a beacon-IE stego payload, a
credential typed into a captive portal, a MSCHAPv2 response, a probe-
request preferred-network entry, a specific reason code in a captured
deauth). Where a puzzle *does* require a LAN pivot, that's a general
network-attack skill served better by tools outside this MCP; P1N3NUT5's
job is to hand off cleanly (a decrypted pcap, a working STA, a captured
credential) and not sprawl.

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
- `karma_family` — KARMA, MANA, MANA Loud, Known Beacons, Snoopy,
  PineAP's implementation choices mapped to each family member
- `default_psk` — vendor default-PSK derivation algorithms
  (UPC/UBEE, BT Home Hub, Thomson Speedtouch, Sagemcom, Technicolor,
  Livebox, Sky, Netgear, etc.) — passive, keyless recovery when the
  vendor is identifiable from beacon
- `chipset_vuln` — silicon-specific flaws (Broadpwn, Kr00k on
  Broadcom/Cypress, Realtek stack overflows, ThreadX-family bugs)
- `client_fingerprint` — probe-request IE ordering, extended-caps bit
  patterns, sequence-number continuity across MAC randomizations,
  per-OS randomization schedules
- `roaming` — 802.11r (FT), 802.11k (neighbor reports), 802.11v (BTM),
  ANQP/802.11u, Passpoint/Hotspot 2.0 — recon and attack surface
- `dos` — management/control-frame denial-of-service families beyond
  broadcast deauth (auth flood, assoc flood, RTS/CTS NAV, EAPOL-Start
  flood, TIM manipulation, CTS-to-self)
- `bibliography` — canonical sources with pinpoint cites

The knowledge-retrieval MCP tools (`lookup_standard`, `lookup_frame`,
`lookup_ie`, `lookup_cipher`, `lookup_eap`, `lookup_attack`,
`lookup_cve`, `lookup_hashcat_mode`, `verify_claim`, `explain_attack`,
`lookup_default_psk`, `lookup_chipset_vuln`, `lookup_fingerprint`)
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

11. **`cracking-tradecraft/`** — beyond `rockyou.txt`. `reference.md`:
    mask attack syntax (`-a 3 ?d?d?d?d?l?l?l?l`), rule stacking
    (`best64`, `d3ad0ne`, `OneRuleToRuleThemAll`), rule-writing basics,
    session save/resume, `--restore`. `walkthrough.md`: SSID-derived
    wordlists (`crunch`, `cewl`, `psudohash`), con-attendee first-name
    lists, hybrid attacks, distributed cracking via hashtopolis, GPU
    tuning (`-w 4 -O`, workload profiles), PMKID vs 4-way crack-cost
    comparison on the same PSK.

12. **`enterprise/`** — WPA2/WPA3-Enterprise. Full topic, not a
    footnote. `reference.md`: 802.1X framing, EAPOL-Start,
    EAP-Request/Response/Success/Failure, inner/outer method model,
    RADIUS-side capture. `walkthrough.md`: rogue-RADIUS with
    `hostapd-wpe` or `eaphammer`, inner-method downgrade (PEAP →
    MSCHAPv2 → GTC), cert phishing against clients with weak validation,
    asleap/hashcat MSCHAPv2 crack, EAP-GTC token capture (RSA / Duo /
    Yubico OTP surfacing inside a rogue tunnel), MDM device-profile
    theft via captive portal ("please reinstall the WiFi profile").
    `recognition.md`: distinguishing PEAP / EAP-TTLS / EAP-TLS /
    EAP-FAST / EAP-PWD / EAP-MD5 / LEAP by outer-fragment behavior and
    initial EAP-Request identity string; spotting cert-pinning holes;
    ANQP-leaked realm hints.

13. **`karma-family/`** — the attack family tree PineAP implements one
    subset of. `reference.md`: KARMA (Dai Zovi & Dinodai, 2004) — probe
    response to any request. MANA (SensePost, 2014) — per-STA SSID
    pools. MANA Loud — union broadcast of all seen probes. Known
    Beacons (Godsend, 2018) — beacon a dictionary of common SSIDs to
    farm associations. Snoopy — geographic tracking via probe
    correlation. `walkthrough.md`: mapping PineAP's karma-toggle /
    allow-associations / SSID-pool settings to each family member;
    when to switch modes. `recognition.md`: distinguishing family
    members from a WIDS console's perspective.

14. **`default-psk-derivation/`** — the "no packets sent" attack. Some
    vendors ship default PSKs derived deterministically from BSSID /
    SSID / serial. If you can identify the vendor from the beacon, you
    already have the PSK. `reference.md`: known-vulnerable vendor +
    firmware generation tables — UPC/UBEE (`upc_keys`), Thomson
    Speedtouch (SSID-suffix hash), BT Home Hub, Sky Broadband, Livebox
    (Sagemcom), Netgear "Genie" default, Airties, Technicolor.
    `walkthrough.md`: identify vendor from beacon (WPS Manufacturer /
    Model IE, OUI, default-SSID prefix regex); run the derivation;
    validate against a captured PMKID or handshake. `recognition.md`:
    "if the SSID matches `/^UPC\d{7}$/` you're one command from a
    candidate PSK list — no radio time required."

15. **`post-crack-rf/`** — the last-mile once you have a PSK or an
    EAP credential. Strictly RF-adjacent, no LAN spillover.
    `reference.md`: driving `wpa_supplicant` / `iwd` from the Pineapple
    with a cracked PSK; Wireshark `wlan.enable_decryption` PSK vs
    PTK-per-session; extracting the 4-way handshake needed to derive
    PTK for a specific STA. `walkthrough.md`: given `capture.pcapng` +
    recovered PSK, decrypt all frames belonging to STA X; validate an
    unknown PSK by trial-decryption of an existing capture; join the
    target network as a legitimate STA to verify the flag is the
    credential itself. `recognition.md`: knowing when the crack is
    "done enough" to hand off — the captured M2 or PMKID is what
    matters, not the association state.
    **Explicit scope stop:** this topic ends at "you are on the
    network." Kerberoasting, Responder, mitm6, SMB, LDAP, service
    scans — all out. If a WCTF flag lives past this line, that's a
    LAN pentest problem outside P1N3NUT5.

### Tier 1.5 — frontier research (2019–2024, write in the same pass as Tier 1)

The competitive difference between a script-kiddie assistant and a real
WCTF operator lives here. Author these to the same depth as Tier 1.

16. **`kr00k/`** — Kr00k (ESET, 2019, CVE-2019-15126). Broadcom/Cypress
    (and later Qualcomm variant) chipsets, upon disassoc, encrypt a
    handful of queued frames with an **all-zero PTK**. Trivial
    decryption of tail traffic. `reference.md`: the disassoc trigger,
    the chipsets/firmware ranges affected, the tail-frame count, the
    2020 QCA variant CVE-2020-3702. `walkthrough.md`: forced disassoc +
    airodump capture + Wireshark decryption with all-zero key. Public
    PoC: ESET's kr00k detector. `recognition.md`: which classes of
    device (older iPhones, Amazon Echo, Kindle, many WiFi cameras) are
    still vulnerable in 2026. Companion `attacks.json` record;
    `cves.json` records for both CVEs.

17. **`ssid-confusion/`** — SSID Confusion (Vanhoef & Yseboodt, 2024,
    CVE-2023-52424). Client believes it's connected to network X but
    is actually on network Y because the SSID isn't authenticated in
    the 4-way handshake. Bypasses VPN auto-connect logic and
    trust-on-SSID heuristics. `reference.md`: the standard flaw
    (`802.11-2020` §12 doesn't include SSID in the PTK derivation),
    the attack primitive, mitigation status per client OS as of 2026.
    `walkthrough.md`: setting up the confused pair; validating with a
    client-side VPN that auto-connects on a "trusted" SSID.
    `recognition.md`: how a WIDS would see this vs. a plain evil twin
    (it wouldn't — that's the point).

18. **`framing-frames/`** — Framing Frames (Vanhoef, 2023). Queueing
    attacks against 802.11 power-save; bypasses several client-
    isolation mechanisms and lets an attacker inject frames destined
    for a sleeping victim. `reference.md`: power-save state machine
    abuse, TIM/DTIM manipulation. `walkthrough.md`: forcing a target
    into deep sleep, poisoning its power-save queue, waking it, and
    reading its response. Public PoC repo. `recognition.md`: signs
    that a client-isolation-enabled AP is still vulnerable.

19. **`macstealer/`** — MacStealer (Vanhoef, 2023). Client-side flaw
    allowing an attacker on the same network to hijack traffic based
    on MAC. `reference.md`: the primitive; which clients are patched
    as of 2026. Companion record.

20. **`mc-mitm/`** — Multi-Channel MitM. The primitive KRACK is built
    on but useful standalone in modern evil-twin work when a target
    supports band-steering / 802.11k / 11v-driven roams. `reference
    .md`: rogue channel selection, forcing a target to switch bands,
    interposing on 5→2.4 GHz roams. `walkthrough.md`: setup on the
    Pineapple's dual radios (2.4 + 5 GHz simultaneously).

21. **`fast-transition/`** — 802.11r/k/v attack surface, thoroughly.
    `reference.md`: FT handshake (initial mobility domain association
    + reassociation), PMK-R0 / PMK-R1 hierarchy, BTM (802.11v BSS
    Transition Management) request/response, 802.11k Neighbor Report.
    `walkthrough.md`: **FT-handshake capture and crack** — an
    FT-roam PMKID-analogue that hashcat mode 22000 handles;
    **BTM-forced roam** — spoofing a BTM Request to shove a client
    onto your rogue BSSID; **spoofed Neighbor Reports** to steer.
    `recognition.md`: identifying FT-capable APs (RSN MDE IE), reading
    the mobility domain field, seeing 11k/11v support bits in Extended
    Capabilities.

22. **`hotspot2/`** — 802.11u, ANQP, Passpoint. Not a rabbit hole,
    but a strategic wedge: **ANQP queries let you probe an AP for its
    Realm List and Roaming Consortium before associating** — huge
    recon win. `reference.md`: ANQP element IDs (NAI Realm, Roaming
    Consortium, Venue Info, 3GPP Cellular Network, Domain Name),
    GAS Initial Request/Response, Passpoint OSU. `walkthrough.md`:
    querying with `hostapd_cli` or scapy; spoofing a Roaming
    Consortium OI to auto-associate Passpoint clients without ever
    broadcasting a matching SSID. `recognition.md`: telltale ANQP-
    Capable bit in Interworking IE.

23. **`wifi6-6e/`** — 802.11ax and Wi-Fi 6E. `reference.md`: OFDMA
    Resource Units, MU-MIMO uplink, TWT (Target Wake Time), trigger
    frames, HE Capabilities IE, HE Operation IE, 6 GHz operating
    class 131–137, Reduced Neighbor Report (RNR) — **6 GHz APs
    advertise themselves via RNR IEs in 2.4/5 GHz beacons**, so you
    can enumerate 6 GHz targets from a card that can't tune 6 GHz.
    `walkthrough.md`: TWT abuse (force client into extended sleep),
    RU-based DoS, RNR-driven 6 GHz recon, exploiting the 6 GHz
    **WPA3-only mandate** — every 6 GHz attack reduces to Dragonblood-
    family reasoning. `recognition.md`: how to tell a 6 GHz-capable
    AP from a beacon in the 5 GHz band.

24. **`wifi7-mlo/`** — 802.11be, Multi-Link Operation. One client on
    2.4/5/6 GHz simultaneously via a single association. `reference
    .md`: MLD (Multi-Link Device) architecture, link setup, per-link
    security context, the shared PTK across links. `walkthrough.md`:
    early attack research (2024–2026 papers), link-desynchronization
    primitives, MLD-address vs link-address exposure. `recognition
    .md`: EHT Capabilities IE, MLD MAC in beacon.

25. **`dragonblood-deep/`** — extends the `dragonblood/` Tier 2 topic
    with **modern SAE follow-ups** — SAE-PT (Password Token,
    Dragonblood mitigation), H2E (Hash-to-Element), lingering
    side-channel research on H2E branches, transition-mode downgrade
    attacks refined post-2020. This distinguishes 2019-Dragonblood
    from "everything since." Records in `attacks.json`.

### Tier 2 — historical-but-alive (write next)

26. **`wep/`** — because it *still exists* in the wild.
    `reference.md`: RC4 keystream, IV length, ICV. `walkthrough.md`:
    aircrack-ng FMS/KoreK/PTW; ARP-request replay to accelerate.
    `recognition.md`: WEP-only APs in the beacon (no RSN IE, no
    WPA vendor IE, "Privacy" bit set).

27. **`wps/`** — PIN brute (Reaver, Pixie Dust) **plus the rest of
    the WPS attack surface** that most 2014-era writeups skip.
    `reference.md`: the 8-digit PIN structure (7+1 with checksum,
    split into two halves → 11k trials worst case); the WSC state
    machine (M1–M8); the WPS IE fields in the beacon (Manufacturer,
    Model Name, Model Number — often leaked even with WPS "disabled").
    `walkthrough.md`: `reaver`, `bully`, `pixiewps` for the classic
    online + Pixie Dust paths; **null-PIN attack** (some APs accept
    the empty PIN); **negative-PIN / EAP-WSC state-machine bugs**
    (chipset-specific); **WPS-Locked bypass timing** (locks reset
    after N minutes on many models); **PBC push-button window abuse**;
    **vendor-derivable PIN algorithms** — MAC-derived PINs on Belkin,
    D-Link, some TP-Link generations. Tools: `OneShotPin`, `WPSpin`,
    `hcxlabtool` for aggressive PMKID+WPS capture. `recognition.md`:
    WPS IE in the beacon, WPS Locked bit, WPS Manufacturer leak
    identifying the vendor's PIN algorithm.

28. **`krack/`** — Vanhoef 2017. `reference.md`: the KRACK family
    (CVE-2017-13077…-13088), which reinstall which key, what changes
    on Linux (all-zero PTK). `walkthrough.md`: mitm attack setup on
    a stack we know is vulnerable. `recognition.md`: whether a client
    is patched (rare in 2026, but not zero on embedded).

29. **`fragattacks/`** — Vanhoef 2020. `reference.md`: 12 CVEs,
    fragmentation cache, mixed-key attack. `walkthrough.md`: crafted
    frame sequences. `recognition.md`: patching status by vendor.

30. **`dragonblood/`** — Vanhoef+Ronen 2019, side-channel + timing
    against WPA3-SAE. `reference.md`: MODP-group selection oracle,
    Brainpool timing. See also `dragonblood-deep/` (Tier 1.5) for
    the post-2020 SAE-PT / H2E follow-up research.

31. **`dos/`** — management + control-frame DoS families beyond the
    plain broadcast deauth. `reference.md`: `mdk4` mode catalog
    (a = auth flood, p = probe flood, d = deauth, b = beacon flood,
    v = RTS/CTS NAV, m = Michael countermeasure — TKIP-only), plus
    EAPOL-Start flood, assoc-request flood, TIM/DTIM poisoning,
    CTS-to-self self-silencing, malformed-IE crash-boots (some
    clients still oom on giant Vendor-Specific IEs). `walkthrough.md`:
    running each; distinguishing "the AP crashed" from "the AP
    ignored me." `recognition.md`: WIDS signatures for each family;
    when a DoS pattern is a *flag signal* rather than a technique
    (some WCTF puzzles use "seen a Michael MIC failure" as a flag
    trigger).

### Tier 3 — hardware, OpenWRT, and the toolchain

32. **`pineapple-mk7/`** — the device itself. `reference.md`: hardware
    (dual radios, USB tether, 2.4/5GHz split, LEDs), stock firmware
    modules, storage, LEDs. `walkthrough.md`: fresh setup, key
    upload, factory reset from a wedged state. `recognition.md`: is
    my Pineapple in a good state? — a checklist.

33. **`pineapple-modules/`** — the third-party module ecosystem. First-
    party PineAP is its own topic; this one covers what the community
    ships and what P1N3NUT5 shells out to. `reference.md`: module
    directory layout, `bootstrap.sh` conventions, log paths.
    `walkthrough.md`: install/enable/uninstall via the API; running
    community modules (Recon Analyzer, Site Survey, evil-portal,
    dwall, EAPHammer wrapper, key-manager) from a scripted engagement.

34. **`openwrt/`** — the userland. `reference.md`: UCI, `hostapd`,
    `wpa_supplicant`, `iw`, `iwconfig` (legacy but present), `logread`,
    `procd`, the filesystem layout. `walkthrough.md`: common UCI
    recipes adjacent to WCTF work (dump current AP config, disable a
    running service, force channel, monitor-mode setup on unusual
    chips).

35. **`hostapd/`** — the AP daemon. `reference.md`: config directives
    cross-referenced against security modes, driver quirks on
    mac80211/ath9k/ath10k/mt76. `walkthrough.md`: build a rogue AP
    with WPA2-Enterprise pointing at a mock RADIUS; WPA3-SAE + PMF-
    required rogue AP for capturing SAE commits during downgrade
    attacks.

36. **`hostapd-wpe/`** — Wireless Pwnage Edition. The canonical
    rogue-AP-with-inner-EAP-capture patchset. `reference.md`: what
    WPE adds (challenge/response logging, MSCHAPv2 capture, EAP-GTC
    plaintext capture, PEAPv0/v1 inner-method downgrade knobs).
    `walkthrough.md`: dropping `hostapd-wpe` on the Pineapple,
    pointing a target enterprise client at it, harvesting the
    challenge/response pair, running asleap or hashcat mode 5500.

37. **`eaphammer/`** — Gabriel Ryan's tool; the modern enterprise
    evil-twin standard. `reference.md`: profile system, cert
    generation, hostile portal templates, silent inner-EAP downgrade
    logic. `walkthrough.md`: end-to-end capture of PEAP-MSCHAPv2
    creds against a target with weak cert validation; running a
    cert-phishing operation; the `--auth` and `--negotiate downgrade`
    flags.

38. **`freeradius-wpe/`** — the RADIUS-side twin of hostapd-wpe when
    you want a real RADIUS on the back end (e.g. an EAP-PEAP outer
    that forwards to a MSCHAPv2 inner and logs both sides).
    `reference.md`: config diff vs stock freeradius. `walkthrough.md`:
    standalone RADIUS harvester.

39. **`hcx-tools/`** — `hcxdumptool`, `hcxpcapngtool`, `hcxlabtool`,
    and how they supplanted the aircrack-ng workflow for handshake +
    PMKID capture. `reference.md`: command surface, output formats,
    hashcat 22000 integration, `hcxlabtool` aggressive-capture mode.
    `walkthrough.md`: full pipeline from air to cracked, including
    the ESSID/BSSID filter list format that PineAP mirrors.

40. **`wifite2/`** — the auto-orchestrator most CTF beginners reach
    for. `reference.md`: what wifite2 automates and where it stops.
    `walkthrough.md`: driving wifite2 from the Pineapple; the assistant
    should be able to beat wifite2 on any target wifite2 handles, and
    know when wifite2 will fail (PMF-required, WPA3-only, transition-
    mode edge cases).

41. **`airgeddon/`** — TUI orchestrator; still widely used. Same
    reference-and-walkthrough shape as wifite2; the assistant should
    be able to explain and outperform.

42. **`fluxion/`** — captive-portal-phishing focus. `reference.md`:
    the fluxion attack chain (deauth → evil twin → captive portal →
    PSK-guess validation via captured handshake). `walkthrough.md`:
    what P1N3NUT5 does better (native Pineapple hostapd + evil-portal
    module vs fluxion's laptop-only design).

43. **`wifipumpkin3/`** — modern successor to WiFiPumpkin; captive-
    portal + template ecosystem. `reference.md`: plugin surface,
    template format. `walkthrough.md`: importing WP3 portal templates
    into the Pineapple's evil-portal module.

44. **`bettercap/`** — the Swiss army knife's wifi module.
    `reference.md`: `wifi.recon`, `wifi.deauth`, `wifi.assoc`,
    `wifi.ap`, `wifi.handshakes`, `wifi.client.probe`, session-file
    format. `walkthrough.md`: bettercap-driven recon + PMKID from the
    Pineapple's SSH; comparing bettercap output to `iw dev` + hcxtool.

45. **`kismet/`** — the standard passive collector. `reference.md`:
    GPS integration, live probe-request DB, rogue-AP detection engine,
    alerts, the Kismet REST API, `.kismet` DB schema. `walkthrough.md`:
    running kismet server on the Pineapple, pulling the DB back for
    offline probe-request analysis; kismet-driven wardriving with GPS.

46. **`iwd/`** — the systemd-native wireless stack, increasingly the
    client-side default on modern Linux (Fedora, Arch, some IoT).
    `reference.md`: how iwd differs from wpa_supplicant under attack
    conditions (state machine, retry behavior on 4-way failure,
    PMF handling). `recognition.md`: distinguishing iwd from
    wpa_supplicant clients by observed behavior.

47. **`scapy-80211/`** — arbitrary 802.11 frame crafting from Python.
    `reference.md`: the `Dot11`/`Dot11Beacon`/`Dot11Elt`/`Dot11Auth`
    class tree, `RadioTap()`, injecting via a monitor-mode iface
    (`sendp`). `walkthrough.md`: one-off crafted-frame recipes the
    plan's `packet_inject` tool wraps — spoofed BTM Request, custom
    beacon with hidden IE payload, ANQP query construction.

48. **`hardware-and-antennas/`** — because tuning matters at a con.
    `reference.md`: dipole vs panel vs yagi vs biquad, 2.4/5/6 GHz
    antenna sizing, dBi vs dBd, directional aiming to isolate a
    target from a scrum of nearby APs. Adapter chipset table:
    Alfa AWUS036AC*, AWUS036AXML, Panda Wireless, tp-link
    Archer T2U/T3U — chipset → monitor/injection support in 2026.
    `walkthrough.md`: rehoming Pineapple antenna choices for a con
    floor vs a bench; TX power caps by region.

49. **`chipsets/`** — silicon-specific behavior on both sides of the
    air. `reference.md`: driver behavior — ath9k (reliable inject),
    ath10k firmware limitations, ath11k (Wi-Fi 6E), mt76 quirks,
    Realtek 88XX driver landscape, Intel iwlwifi (monitor-mode
    inability on many revs). Client-side: Broadcom-family chips
    (Kr00k, Broadpwn history), Cypress inheritance, Qualcomm Atheros,
    MediaTek. `walkthrough.md`: identifying an AP's chipset from
    beacon + WPS IEs + rate set; identifying a client's chipset from
    probe-request IE order and OUI.

### Tier 4 — perception & analysis

50. **`pcap/`** — how we read a capture. `reference.md`: pcap vs
    pcapng, radiotap headers, common filter recipes. `walkthrough.md`:
    tshark one-liners for AP enumeration, handshake completeness,
    probe-request profiling, `wlan.enable_decryption` with a recovered
    PSK for per-STA PTK derivation.

51. **`fingerprinting/`** — a full discipline, not one bullet. Two
    sub-axes: **client fingerprinting** (probe-request IE ordering,
    extended-capabilities bit patterns, supported-rates set,
    sequence-number continuity across MAC randomizations, per-OS
    randomization schedules — iOS 14+ per-SSID, Android 10+ per-SSID
    with vendor variants, Windows 10/11 per-connection, macOS
    Sonoma changes) and **AP fingerprinting** (see next topic).
    `reference.md`: what varies at the byte level; fingerprint
    databases (Wireshark IEEE OUI, hoover-style probe DBs, community
    fingerprint tables); GAS/ANQP query fingerprinting.
    `walkthrough.md`: identifying an iPhone vs a Samsung TV vs a
    Raspberry Pi from probes alone; correlating a client across
    randomized MACs using seq-num + IE-order continuity.
    Records in `client_fingerprints.json`.

52. **`ap-fingerprinting/`** — the first-60-seconds triage skill.
    `reference.md`: beacon Vendor-IE OUI + subtype patterns per
    vendor; beacon-interval / DTIM patterns per firmware; rate-set
    signatures; **WPS Manufacturer / Model Name / Model Number IEs
    that many APs leak even with WPS disabled**; Wi-Fi Alliance
    certification database cross-reference from beacon; RSN IE
    ordering quirks per driver. `walkthrough.md`: `beacon_diff` on
    a suspected evil twin; identifying the AP's chipset and firmware
    family from the beacon alone, no active probe.

53. **`ies/`** — Information Elements as a first-class topic. Every
    IE the assistant will ever see, incl. Interworking / ANQP /
    Roaming-Consortium / HE Capabilities / EHT Capabilities / MDE
    (FT) / RNR / Reduced Neighbor Report / MLD MAC. Backed by
    `records/ies.json`.

### Tier 5 — CTF-facing (the P1N3NUT5 analog of PHR34CKER5's `ctf/`)

54. **`ctf/`** — one file per WCTF puzzle subgenre:
    - `strategy.md` — first-60-seconds recon prioritization; how to
      rank targets by "flag likelihood" (WPS-on APs, PMKID-leaking
      APs, vendor-default-SSID APs, transition-mode APs, PMF-off
      APs, exotic-IE APs); which puzzles are single-operator vs
      require a two-op recon/attack split.
    - `scoring-recon.md` — WCTF scoring bots ping their own flag
      traps to verify uptime; you can passively detect scorers from
      their probe patterns and use that to identify which APs are
      *the* target APs vs decoys. Also: time-based puzzles that only
      surface a flag in specific windows.
    - `hidden-ssid-mazes.md` — SSIDs revealed only in probe responses
    - `pmf-required-targets.md` — how to work around PMF (or not);
      unicast-deauth on PMF-disabled clients in transition-mode
      networks; when to switch to SSID Confusion or MC-MitM instead
    - `wpa2-crack-flags.md` — the classic "PSK is the flag"
    - `wpa3-transition-downgrade.md` — PMK from the WPA2 side of a
      transition-mode AP
    - `default-psk-flags.md` — vendor beacon + `upc_keys`-family
      derivation = PSK, no radio time. Common WCTF sleeper puzzle.
    - `pmkid-fastpath.md` — a PMKID-leaking AP is often the fast lane
    - `evil-twin-farms.md` — a WCTF that gives you many APs and one
      is the trap
    - `captive-portal-cred-flags.md` — the flag is what a user types
    - `rogue-radius-eap-flag.md` — the flag is a MSCHAPv2 password
      or the plaintext GTC token a rogue-tunnel client hands you
    - `cert-phish-eap-flags.md` — enterprise clients with weak cert
      validation reveal a flag once they associate to your rogue
      RADIUS
    - `beacon-flag-stego.md` — the flag is hidden in beacon IEs
      (Vendor-Specific, custom IE ID, hidden inside an SSID
      encoding, hidden across DTIM timing)
    - `probe-request-flag.md` — a rogue client is leaking the flag in
      its preferred-network list
    - `deauth-forensics.md` — the flag is a specific reason code in a
      seen deauth frame, or a signature in the pattern of a deauth
      storm
    - `wps-pin-flag.md` — WPS is on, brute the PIN (Pixie Dust,
      null-PIN, vendor PIN derivation)
    - `ft-handshake-flag.md` — capture an 802.11r roam and crack the
      FT-derived material with hashcat 22000
    - `hotspot2-anqp-flag.md` — the flag is embedded in an ANQP
      element (NAI Realm string, Venue Info); recover with a GAS
      query, no association needed
    - `kr00k-tail-flag.md` — force disassoc on a Kr00k-vulnerable
      client and read the tail-frame plaintext
    - `ssid-confusion-flag.md` — the flag is what a client sends when
      it believes it's on network X but is really on Y
    - `wifi6e-6ghz-flag.md` — the flag lives on a 6 GHz-only AP
      (WPA3-mandated); enumerate via RNR from a 2.4/5 GHz beacon
    - `wifi7-mlo-flag.md` — the flag exploits a Multi-Link Operation
      desync between the client's 2.4/5/6 GHz links
    - `framing-frames-flag.md` — power-save queue poisoning against a
      client in deep sleep
    Each: what it looks like in the first 60 seconds on the recon
    display, how to probe it, which MCP tools to reach for, common
    flag-hiding patterns.

### Tier 6 — glossary and orientation

55. **`glossary/`** — SSID, BSSID, MAC randomization, RSSI, MCS, IE,
    KMP, PMK, PTK, GTK, PMKID, ANonce/SNonce, MIC, PN, EAPOL-Key,
    OWE, SAE, SAE-PT, H2E, PMF, MFP, MLD (Wi-Fi 7), TWT, RU (OFDMA),
    RNR, MDE (802.11r), BTM (802.11v), ANQP, GAS, Passpoint, WIDS,
    hcxdumptool, aircrack-ng. Growing.

56. **`zines-and-talks/`** — the DEFCON/BSides/CCC talk canon:
    Cache 2001 WEP paper, Wright & Cache "Hacking Exposed Wireless",
    Wright's `asleap`, Vanhoef's whole run (KRACK 2017, Dragonblood
    2019, FragAttacks 2020, Framing Frames 2023, MacStealer 2023,
    SSID Confusion 2024), Steube's PMKID advisory, ESET's Kr00k
    disclosure, Gabriel Ryan's `eaphammer` talks, SensePost's MANA
    original writeup. `reference.md`: table of landmark talks with
    URLs, DOIs, GitHub repos. Pointers, not paraphrase.

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
| `default_psks.json` | `default_psk` | vendor default-PSK derivation algorithms (UPC/UBEE, Speedtouch, BT Home Hub, Sky, Sagemcom, Livebox, Netgear, Airties, Technicolor), keyed by beacon-observable vendor fingerprint |
| `chipset_vulns.json` | `chipset_vuln` | silicon-specific flaws — Kr00k (Broadcom/Cypress/QCA), Broadpwn, Realtek RTL87xx family, ThreadX/NetX-Duo bugs, driver-side monitor/injection quirks |
| `client_fingerprints.json` | `client_fingerprint` | probe-request IE ordering signatures, per-OS randomization schedules, seq-num continuity heuristics |
| `karma_family.json` | `karma_family` | KARMA / MANA / MANA Loud / Known Beacons / Snoopy — with which PineAP configuration implements each |
| `roaming.json` | `roaming` | 802.11r/k/v + 802.11u/ANQP/Passpoint attack + recon surface |
| `dos.json` | `dos` | management/control-frame DoS families (mdk4 mode catalog, EAPOL-Start flood, TIM/DTIM poison, CTS-to-self, Michael-MIC) |
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
- **"Kr00k only affects old devices."** Partial. The core Broadcom /
  Cypress bug (CVE-2019-15126) is largely patched on flagship phones
  by 2026 but persists on many IoT endpoints (older Amazon Echo,
  Kindle, WiFi cameras, older iPhones/iPads not upgraded). The QCA
  variant CVE-2020-3702 has a longer tail. Records enumerate
  vulnerable ranges.
- **"SSID Confusion needs the target PSK."** No — the attack
  (Vanhoef & Yseboodt 2024, CVE-2023-52424) works because the SSID
  is not authenticated in the 4-way handshake at all. The client is
  fooled about *which* network it's on; the PSK is whatever it
  actually is on each side.
- **"802.11r Fast Transition is more secure because it's newer."**
  Partial. FT roams can leak an M1-analog PMKID that hashcat mode
  22000 handles; misconfigured 11r deployments can share PMK-R0
  material across BSSIDs, which turns one crack into a whole-fleet
  compromise.
- **"11k neighbor reports and 11v BTM are informational only."** No —
  both can be spoofed. A crafted BTM Request from a rogue can shove
  a client onto an attacker BSSID with the client's cooperation.
- **"6 GHz is safe because WPA3-only."** Partial. WPA3-only closes
  the WPA2 downgrade door, but Dragonblood-family side channels
  still apply where the SAE implementation is weak. And RNR IEs in
  2.4/5 GHz beacons often advertise the 6 GHz BSSIDs to attackers
  without 6 GHz radios.
- **"Wi-Fi 7 MLO is a wired-quality secure channel."** No — the
  shared-PTK-across-links model creates new desync primitives; 2024
  research is publishing them.
- **"Hidden SSIDs are recovered by deauthing clients."** Partial —
  clients whose config auto-reconnects usually name the SSID in the
  next probe request, but modern OS behavior (per-SSID randomization
  + WPA3 preferring passive discovery) has thinned the pool.
- **"Default-PSK derivation is a 2010s problem."** No — vendor
  default PSKs still ship on new 2024–2025 consumer gear in EU/UK
  markets (UPC/UBEE mesh gear, Sky Broadband hubs, BT SmartHub
  generations). If the SSID matches a known-vendor regex, the
  derivation is often still valid.
- **"WPS is deprecated so no one has it on." / "Reaver always works."**
  Both wrong at opposite extremes. WPS is off on flagship consumer
  gear by 2026 but still on in enterprise-branded consumer gear and
  ISP-supplied routers. And when it's on, vendor lockout and
  WPS-Locked timing are chipset-specific — record enumerates
  vendor+chipset current-status.
- **"hostapd-wpe and eaphammer are the same tool."** No — WPE is the
  patch to hostapd for inner-EAP logging; eaphammer is a higher-
  level orchestrator that generates certs, templates hostile portals,
  and drives multiple attack profiles. Records for each.

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
    (FragAttacks), CVE-2011-5053 (WPS PIN), CVE-2019-15126 (Kr00k
    Broadcom/Cypress), CVE-2020-3702 (Kr00k QCA variant),
    CVE-2023-52424 (SSID Confusion), CVE-2017-11120 (Broadpwn),
    CVE-2021-28492 (Realtek RTL87xx family).
28. **Vanhoef, Yseboodt (2024)** — SSID Confusion, USENIX Security /
    disclosure @top10vpn co-publication.
29. **Vanhoef (2023)** — Framing Frames, USENIX Security 2023 (power-
    save queue attacks); MacStealer companion paper.
30. **ESET (2020)** — Kr00k white paper and detector release.
31. **SensePost — Wilhelm & de Ruiter (2014)** — MANA attack original
    Defcon 22 / BlackHat writeup.
32. **Godsend (2018)** — Known Beacons attack, WPA-Sec presentation.
33. **Gabriel Ryan (2017–2020)** — `eaphammer` release + associated
    DEFCON/BSides talks on cert-phish and inner-EAP downgrade.
34. **Bongard / stkeys / upc_keys** — vendor default-PSK derivation
    code repositories; keep the URL pinned in `bibliography.json`
    even when repos churn.
35. **Wi-Fi 7 (802.11be) early-attack papers (2024)** — MLO link-
    desync research; whichever paper is most-cited by DEFCON WCTF
    2026 organizers becomes the anchor cite in `wifi7-mlo/`.

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
- **2014 — SensePost MANA.** KARMA reborn with smarter probe-response.
- **2017 — Vanhoef/Piessens KRACK.** Every WPA2 client patched over
  the next 24 months.
- **2017 — Broadpwn (Artenstein, CVE-2017-11120).** Broadcom SoC RCE
  from the air.
- **2018 — Steube PMKID.** Client-free WPA2-PSK capture.
- **2018 — Wi-Fi Alliance certifies WPA3.**
- **2018 — Godsend "Known Beacons" attack.** KARMA-family SSID
  dictionary broadcast harvests associations.
- **2019 — Vanhoef/Ronen Dragonblood.** WPA3-SAE gets a black eye.
- **2019 — ESET Kr00k (CVE-2019-15126).** Broadcom/Cypress all-zero
  PTK on disassoc — millions of devices, decrypt-in-the-clear tail.
- **2020 — 802.11ax (Wi-Fi 6) rollup.**
- **2020 — 6 GHz opened (US), Wi-Fi 6E.** WPA3-only mandate.
- **2020 — QCA Kr00k variant (CVE-2020-3702).**
- **2021 — Vanhoef FragAttacks.** Twelve CVEs.
- **2023 — Vanhoef Framing Frames.** Power-save queue attacks
  bypass client isolation.
- **2023 — Vanhoef MacStealer.**
- **2023 — Realtek RTL87xx wireless stack overflows (CVE-2021-28492
  family, disclosed 2021–2023).**
- **2024 — Vanhoef & Yseboodt SSID Confusion (CVE-2023-52424).**
  The 4-way handshake doesn't authenticate the SSID.
- **2024 — Wi-Fi 7 (802.11be) products ship;** first MLO desync
  research surfaces.
- **2026 — DEF CON WCTF.** The corpus's date target.

Every DEFCON WCTF talk sits in this timeline; every attack record
carries the paper year in `era_bounds`.

---

## Authoring order — why order matters

The records aren't independent. Each record's `citations[]` field
must point to an id that already exists in `bibliography.json`, and
`see_also[]` fields chain records together (an `attacks.json` entry
points at a `cves.json` entry which points at a `security_suites.json`
entry which points at a `standards.json` entry). The loader is strict
about this — if you author `attacks.json` first and try to cite a
paper that isn't in `bibliography.json` yet, the loader raises and
nothing loads.

So author the records in **dependency order**: foundations first,
things-that-cite-foundations next, things-that-cite-those last. Inside
each layer, the order doesn't matter and files can be authored in
parallel. The layers are:

**Layer 0 — foundation (no dependencies, must exist first):**
1. `bibliography.json` — every paper, RFC, standard, CVE Mitre entry,
   GitHub repo, vendor doc that anything else will cite. Author this
   first; nothing else can be validated until this exists.
2. `standards.json` — 802.11 amendments, 802.1X, key RFCs. Cites
   `bibliography.json`, cites nothing else.
3. `channels.json` — pure regulatory data, only cites
   `bibliography.json` (spec sections + FCC/ETSI/MIC docs).
4. `hashcat_modes.json` — pure mode-number reference, cites hashcat
   docs + Steube's original PMKID advisory in `bibliography.json`.

**Layer 1 — 802.11 primitives (cite Layer 0):**
5. `frame_types.json` — cites `standards.json` (§9 of 802.11-2020) and
   `bibliography.json`. Frame types don't reference each other.
6. `ies.json` — cites `standards.json` and `frame_types.json` (each IE
   appears in specific frame types). Sub-order inside this file
   doesn't matter, but author basic IEs first (SSID, RSN, HT/VHT/HE
   Capabilities) before frontier IEs (Interworking/ANQP elements,
   MDE, RNR, MLD MAC).
7. `security_suites.json` — cites `standards.json` and `ies.json`
   (RSN cipher suites live in the RSN IE).
8. `eap_methods.json` — cites `standards.json` (802.1X, EAP RFCs).
   Leave the `attacks[]` back-references for a Layer-3 pass.

**Layer 2 — the CVE ledger (cites Layer 0 + Layer 1):**
9. `cves.json` — every wireless CVE. Cites `bibliography.json` and the
   `security_suites.json` / `eap_methods.json` entries the CVE targets.
   Author this before `attacks.json` because many attack records
   `see_also` a specific CVE.

**Layer 3 — the attack catalog (cites everything above):**
10. `attacks.json` — the load-bearing file. Every record here cites
    `bibliography.json` (the paper that first described it), points
    `see_also` at `cves.json` where applicable, references
    `hashcat_modes.json` by mode number, and pins `target_security`
    to `security_suites.json` ids. Author in this sub-order:
    - **10a. Legacy-but-alive** (`wep-*`, `wpa2-4way-capture`,
      `pmkid-capture`, `wps-*`, `krack-*`, `fragattacks-*`) — the
      classic canon. Authoring these first shakes out the schema and
      validator before you're deep in frontier territory.
    - **10b. Frontier** (`kr00k-*`, `ssid-confusion-*`,
      `framing-frames-*`, `macstealer-*`, `ft-*`, `mc-mitm-*`,
      `wifi7-mlo-*`, `dragonblood-*` follow-ups) — the WCTF
      differentiators.
    - **10c. Rogue-AP / KARMA family / enterprise** — depends on the
      first two batches for `see_also` targets.
    - **10d. DoS + management-frame primitives** — mostly self-
      contained but cites `frame_types.json` for the frame each mode
      abuses.
    - **10e. Default-PSK derivations** — depends on `bibliography.json`
      only (the `upc_keys`-family repos), self-contained otherwise.
11. `eap_methods.json` **second pass** — now that `attacks.json` exists,
    fill in each EAP method's `attacks[]` back-references.

**Layer 4 — the operator surface (cite Layer 0–3 as needed):**
12. `pineapple_endpoints.json` — every API path + SSH command the MCP
    calls. Cites Hak5 docs (`bibliography.json`) and `attacks.json`
    where an endpoint's purpose is "invoke attack X" (e.g. the
    `capture_handshake` SSH command → `see_also: wpa2-4way-capture`).
13. `openwrt_uci.json` — OpenWRT userland; cites OpenWRT docs.
14. `defense_and_detection.json` — PMF, WIDS behaviors, evil-twin
    detection. Cites `attacks.json` (each defense counters specific
    attacks) and `standards.json` (PMF = 802.11w).
15. `karma_family.json` — cites `attacks.json` (each family member has
    an `attacks.json` entry) and `pineapple_endpoints.json` (each
    maps to PineAP config).
16. `roaming.json` — cites `attacks.json` (FT capture, BTM spoof) and
    `standards.json` (11r/11k/11v/11u).
17. `dos.json` — cites `attacks.json` and `frame_types.json`.
18. `chipset_vulns.json` — cites `cves.json` (Kr00k, Broadpwn,
    Realtek) and `attacks.json`.
19. `client_fingerprints.json` — cites `ies.json` (probe-request IE
    ordering signatures) and vendor docs in `bibliography.json`.
20. `default_psks.json` — cites `bibliography.json` (derivation-tool
    repos) and, per entry, the vendor's default-SSID regex.

**Layer 5 — prose corpus (writes against records, not the reverse):**
21. `knowledge/<topic>/*.md` files. Every `reference.md` cites at
    least one `bibliography.json` entry. Every `attacks.json` id used
    in a `walkthrough.md` must already exist. Author topics in the
    same tier order the topic list uses (Tier 1 first, then Tier 1.5
    frontier, then Tiers 2–6).

**Layer 6 — validation / testing (runs against everything above):**
22. Test corpus (100 gold Q/A pairs), adversarial corpus (40 traps),
    era/vendor coverage matrix, citation-integrity CI check, fixture
    pcaps.

**Stopping between layers is fine.** Each layer leaves the corpus in
a validator-clean state. If you stop after Layer 3, the MCP already
answers `lookup_attack` / `lookup_cve` / `lookup_standard` for the
authored subset — you don't need Layers 4–6 to ship a useful assistant.

**Parallelism inside a layer is fine.** Layer 0's four files are
independent; Layer 1's four files are independent once Layer 0 is
done; the `attacks.json` sub-batches in Layer 3 are independent once
Layer 2 exists.

---

## Build/populate plan

1. **Schema.** JSON Schemas for each record type. Enforce `citations[]`
   non-empty and every entry resolves to `bibliography.json`. Enforce
   `era_bounds` as `[first_effective, last_effective]` with ISO dates
   or null. Enforce `see_also` targets exist. Build this before any
   record authoring — the schema is what makes wrong-order authoring
   fail loudly instead of silently.
2. **Seed data.** Hand-author the core records in the **layered order
   above**. Target counts per file:
   - ~30 `standards.json` records (every 802.11 amendment through be,
     plus 802.1X, 802.11u, key EAP RFCs, Passpoint spec)
   - ~180 `channels.json` records (every US 2.4 + 5 + 6 GHz channel
     with regulatory status; per-region variants folded in)
   - ~40 `frame_types.json` records (every subtype + a note on where
     it appears)
   - ~80 `ies.json` records (including Interworking, ANQP elements,
     HE/EHT Capabilities, MDE, RNR, MLD MAC — frontier-era IEs)
   - ~35 `security_suites.json` records (RSN cipher suites, AKM
     suites incl. SAE / SAE-EXT-KEY / OWE / FT-PSK / FT-SAE, WEP
     variants)
   - ~30 `eap_methods.json` records — with per-method `attacks[]`
     field pointing back to `attacks.json` (PEAP → inner-downgrade
     attacks; EAP-PWD → Dragonblood; LEAP → asleap; EAP-MD5 → offline
     brute)
   - ~90 `attacks.json` records covering Tier 1, Tier 1.5 (frontier),
     and Tier 2 completely — see Appendix B for the target list
   - ~40 `cves.json` records — KRACK family (12), Dragonblood (2),
     FragAttacks (12), Kr00k (2), SSID Confusion (1), Broadpwn,
     Realtek RTL87xx, WPS PIN, plus PMKID mitigation flags
   - ~30 `hashcat_modes.json` records (the WiFi-relevant subset,
     incl. 22000/22001, 2500/2501, 16800/16801, 5500 for MSCHAPv2)
   - ~60 `pineapple_endpoints.json` records — every API path + SSH
     command the MCP will call, including community-module endpoints
   - ~40 `openwrt_uci.json` records
   - ~25 `defense_and_detection.json` records
   - ~15 `default_psks.json` records (each: vendor, beacon
     fingerprint regex, derivation algorithm, era_bounds,
     still_effective_2026 with vendor-generation notes)
   - ~15 `chipset_vulns.json` records — Broadcom Kr00k, Cypress
     inheritance, QCA CVE-2020-3702, Broadpwn, Realtek family,
     driver monitor/injection matrix
   - ~20 `client_fingerprints.json` records — per-OS randomization
     schedule, probe-IE order signatures, seq-num heuristics
   - ~10 `karma_family.json` records — KARMA, MANA, MANA Loud,
     Known Beacons, Snoopy, each mapped to PineAP config
   - ~15 `roaming.json` records — 11r/11k/11v/11u/Passpoint recon
     and attack surfaces
   - ~15 `dos.json` records — mdk4 mode catalog + EAPOL-Start,
     RTS/CTS, TIM/DTIM, CTS-to-self, Michael-MIC
   No web-scrape auto-generation — every record hand-verified.
3. **Prose corpus.** Author topic dirs in the same tier order the
   topic list uses. Every `reference.md` cites `bibliography.json`;
   every `walkthrough.md` references only `attacks.json` ids that
   exist. Layer 5 of the authoring-order rule.
4. **Test corpus.** ~100 gold-standard Q/A pairs mined from DEFCON
   WCTF write-ups, Wright/Cache, Vanhoef's papers, and hashcat forum
   threads. The assistant + MCP must answer each correctly.
5. **Adversarial corpus.** ~40 trap questions where the "obvious"
   answer is wrong (PMF stops all deauth; WPA3 kills offline attack;
   hidden SSID is secret). `verify_claim` must return the right
   graded verdict.
6. **Era/vendor coverage matrix.** A test that samples the corpus by
   `(era, vendor)` cell and confirms non-empty coverage across the
   {WPA2-era, WPA3-era, Wi-Fi 6/6E-era} × {Cisco, Ubiquiti, TP-Link,
   MikroTik, Ruckus, consumer-mesh} matrix.
7. **Citation integrity.** CI check — every `citations[]` entry
   resolves to a `bibliography.json` id; every `see_also[]` entry
   resolves to a record id in some records file; no orphaned bib
   records. This check runs on every commit; a wrong-order author
   caught here is a small fix, not a rebuild.
8. **Fixture pcaps.** For every `frame_types.json` record and every
   `attacks.json` Tier-1 record, ship a small `.pcapng` fixture under
   `tests/fixtures/` so the perception tools have a deterministic
   parse target. Fixtures are keyed by record id.

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
  `mitigation`, `era_bounds`, `still_effective_2026`,
  `hashcat_mode` (or explicit null), and at least one primary or
  secondary citation.
- 100% of `pineapple_endpoints.json` records have both `firmware_min`
  and at least one of `api` or `ssh` populated.
- 100% of `channels.json` records have per-region regulatory status.
- 100% of ~100 test-corpus questions answered with exact agreement
  (not "roughly WPA3-ish").
- 100% of trap questions result in `verify_claim` returning `false` or
  `needs_qualification` with citations to the correct record.
- **`explain_attack` never refuses on the basis of era or
  `target_security`.** It always returns steps; era/target-security
  become non-blocking context lines in the response envelope. Refusal
  only happens if the claim underlying the request grades `false`
  via `verify_claim`, and even then the refusal cites the record
  and the correct alternative technique.
- **Every Tier 1.5 (frontier) topic ships with a `walkthrough.md`
  even if the walkthrough is 5 lines.** No frontier topic is left as
  a reference-only stub; a WCTF operator needs to know what commands
  to type, not just that the vulnerability exists.
- **The corpus answers every attack record with a plain-English
  1-sentence "what does the flag look like" line.** This is the
  first-60-seconds triage layer; a puzzle's flag pattern is a
  first-class field on every `attacks.json` record where the
  attack has been seen in a WCTF.
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

**Legacy-but-alive:**
- `wep-fms`, `wep-korek`, `wep-ptw`, `wep-arp-request-replay`
- `tkip-beck-tews-mic-recovery`

**WPA2-PSK workhorses:**
- `wpa2-4way-capture`, `pmkid-capture`, `pmk-crack-hashcat`,
  `pmk-crack-mask-attack`, `pmk-crack-hybrid`

**WPS:**
- `wps-reaver-online`, `wps-pixie-dust`, `wps-null-pin`,
  `wps-negative-pin`, `wps-vendor-pin-derivation`,
  `wps-locked-bypass-timing`, `wps-pbc-window-abuse`

**KRACK family (2017):**
- `krack-client-key-reinstall`, `krack-ap-key-reinstall`,
  `krack-linux-all-zero-ptk`, `krack-groupkey-reinstall`

**Dragonblood + SAE follow-ups:**
- `dragonblood-sidechannel`, `dragonblood-timing`,
  `dragonblood-modp-downgrade`, `sae-h2e-followup-side-channel`,
  `wpa3-transition-downgrade`

**Kr00k (2019–2020) — 2026-relevant:**
- `kr00k-broadcom-cve-2019-15126`,
  `kr00k-qualcomm-cve-2020-3702`

**FragAttacks (2020):**
- `fragattacks-mixed-key`, `fragattacks-cache-poisoning`,
  `fragattacks-plaintext-inject`

**Frontier (2023–2024):**
- `ssid-confusion-cve-2023-52424`
- `framing-frames-power-save-poison`
- `macstealer-mac-hijack`
- `wifi7-mlo-link-desync`

**Roaming (802.11r/k/v/u) surface:**
- `ft-handshake-capture`, `ft-r0-shared-fleet-crack`
- `btm-forced-roam`, `neighbor-report-spoof`
- `anqp-realm-enum`, `passpoint-roaming-consortium-spoof`

**MC-MitM primitive:**
- `mc-mitm-dual-radio`

**Deauth / management DoS:**
- `deauth-broadcast`, `deauth-targeted`, `disassoc-targeted`
- `beacon-flood-mdk4`, `probe-flood-mdk4`, `authentication-flood`,
  `association-flood`, `eapol-start-flood`,
  `rts-cts-nav-dos`, `cts-to-self-silencing`,
  `tim-dtim-poison`, `tkip-michael-mic-dos`

**Rogue AP / KARMA family:**
- `evil-twin-clone`, `mana-karma`, `mana-loud`,
  `mana-known-beacons`, `snoopy-track`
- `captive-portal-cred-capture`

**Enterprise (802.1X):**
- `rogue-radius-hostapd-wpe`,
  `rogue-radius-eaphammer`,
  `cert-phish-eaphammer-weak-validation`,
  `eap-inner-downgrade-peap-gtc`,
  `eap-inner-downgrade-peap-mschapv2`,
  `mschapv2-challenge-response-capture`,
  `asleap-mschapv2-crack`,
  `hashcat-5500-mschapv2-crack`,
  `eap-gtc-plaintext-token-capture`,
  `mdm-profile-theft-captive-portal`,
  `leap-legacy-crack`

**Default-PSK (passive, no radio):**
- `default-psk-upc-ubee`,
  `default-psk-thomson-speedtouch`,
  `default-psk-bt-home-hub`,
  `default-psk-sky-broadband`,
  `default-psk-livebox-sagemcom`,
  `default-psk-netgear-genie`,
  `default-psk-technicolor`

**PineAP-specific:**
- `pineap-passive-probe-log`,
  `pineap-active-karma`,
  `pineap-ssid-pool-broadcast`

**Wi-Fi 6/6E:**
- `twt-forced-sleep-abuse`,
  `rnr-6ghz-enumeration`,
  `ru-based-ofdma-dos`

**Frame primitives:**
- `frame-injection-arbitrary`,
  `scapy-crafted-beacon-with-vendor-stego`

**AP-side chipset vulns (era-authentic):**
- `broadpwn-broadcom-cve-2017-11120`,
  `realtek-rtl87xx-cve-2021-28492`

Each with preconditions, hashcat mode (or null), tool chain, era_bounds,
`still_effective_2026`, and citations.
