# field_notes — operator-side, engagement-aware

This is the doc that gets updated at least once a year — venue rules
change, scoring quirks change, RF environments change. It is not
DEF-CON-only; wireless work spans WCTF villages, red-team retainers,
blue-team labs, and home benches, and this MCP is meant for all of
them. Each has different constraints, different success criteria, and
different traps.

Read the section that matches what you're actually doing today.

## Section 0 — engagement matrix

| engagement            | scope                            | authorization pattern                        | success                    |
| --------------------- | -------------------------------- | -------------------------------------------- | -------------------------- |
| WCTF (village)        | Sanctioned airspace, all targets | `i_own_the_airspace=True` for the session    | Flags scored               |
| Red team retainer     | Contract SOW + written scope     | `Authorization(ssid_allowlist, bssid_...)`   | Objectives met, deliverable|
| Blue-team lab / range | You own / rent the RF space      | `i_own_the_airspace=True` (your lab)         | Detection built + validated|
| Home / self-training  | Your own gear only               | `i_own_the_airspace=True` (single-SSID authz)| Skill acquired             |
| Client audit (limited)| Site + assets in writing         | `Authorization(...)` per-target              | Report                     |

If the row for your current work is ambiguous, that is the flag: stop
and get the scope in writing. Wireless is easier than most surfaces to
get illegal on. [`legal_and_consent.md`](legal_and_consent.md) is the
enforcement layer; this table is the mental model that drives which
knob you turn.

## Section 1 — WCTF villages

Every wireless CTF is a village with a scoreboard, a set of built
targets, and rules that are enforced socially more than technically.
The MCP treats "village" as one authorization mode, but the venues
differ in ways that matter operationally.

### 1a — What every village tends to publish

Look for these on the village's page or in the room:

- **Scope of RF activity.** Which SSIDs are the puzzle set, which are
  village infrastructure (scoreboard, tally), which are attendee
  devices. Villages differ on which of these are fair game.
- **Flag format.** Sometimes literal `flag{...}`, sometimes plain
  strings, sometimes MAC addresses, sometimes hex from a beacon IE.
- **Submission conventions.** Case sensitivity, whitespace stripping,
  dup submits, points-per-flag decay.
- **Airspace ground rules.** Broadcast-deauth allowed? Rogue-RADIUS
  allowed? PineAP KARMA-mode allowed against attendee devices?
  These vary; some villages ban KARMA outright against anything not
  advertised as a target.
- **Team size caps and shared-target etiquette.** Some villages allow
  parallel teams to work the same puzzle; some don't.
- **Prize / write-up publication expectations.** If you win, expect to
  be asked for a writeup — this affects how you log the run (see
  [`recipes.md § Bonus — post-engagement audit`](recipes.md)).

### 1b — Village-agnostic operator ops

- Rules and scope live on the village page and change year to year.
  Ambiguous cases → ask staff; getting a "yes it's in scope" up front
  beats getting a DQ later.
- Village infrastructure (scoreboard, tally, staff APs) is usually
  out of scope even at "own the airspace" villages. Same with other
  teams' gear. Confirm at check-in.
- `call_log(ssh=True, api=True)` at end of session — writeup, disputes,
  team debrief all read from it.

### 1c — Known WCTF-flavored venues (2026 snapshot)

Verify against the current year's page before the con. Village staff
rotates; rules do too.

- **DEF CON Wireless Village** — largest US WCTF. See § 5 below for
  the yearly-update block.
- **DEF CON Wi-Fi CTF (occasionally separate).** Some years there is
  a distinct scoring track separate from the Wireless Village. Ask
  at con-time.
- **ShmooCon Wireless CTF.** Smaller, DC-based, January. Historically
  more forensics / decode puzzles, fewer live-crack puzzles.
- **BSides (various)** — many BSides events run a small wireless CTF
  or invite village organizers to run one. Local, short, often the
  best place to try new tools.
- **CactusCon Wireless.** Phoenix. Runs a small WCTF with a
  hands-on lab feel.
- **HackFest Québec / NorthSec (Montréal)** — Wireless tracks appear
  regularly.
- **WOPR / other private events.** Invite / ticket-gated; scope is
  the event airspace only.
- **Pros vs Joes / regional CCDC-adjacent events.** Not pure WCTF but
  wireless is often in play.

If the venue isn't on this list, the questions in § 1a are the same.

## Section 2 — red-team engagements (retainers, on-site audits)

Different constraints from a WCTF: scope is narrower, the target list
is a document, and the deliverable is a report.

### 2a — Scope as code

Convert the SOW into an `Authorization` object; the allowlist refuses
stray targets so a `list_aps` typo doesn't become an incident:

```python
Authorization(
    ssid_allowlist=("acme-corp", "acme-guest"),
    bssid_allowlist=("aa:bb:cc:...", ...),
)
```

SSIDs, BSSIDs (if you have them), MAC prefixes, days/hours, geo — all
live in the SOW. Neighbors' APs will show up in `list_aps`; that's
expected, they're just not in the allowlist.

### 2b — Noise budget

Different SOWs have different noise budgets — some engagements want
you loud enough to test detection, some want you invisible. Rough
noise ranking on the WPA2 lanes:

- **PMKID capture** — quietest. hcxdumptool triggers M1 via ordinary
  association; no deauth needed. WIDS won't usually flag it.
- **Unicast targeted deauth** — one client MAC, a few frames. Small
  footprint.
- **Broadcast deauth** — loud. Wireshark and WIDS both alert on it.
- **Rogue AP / evil twin advertising the client's SSID** — loudest.
  Any WIDS with SSID-uniqueness rules alerts.

Pick the lane that matches the SOW's noise budget; if the SOC is in
on the exercise, coordinate the loud ones.

### 2c — Deliverable-oriented capture

- Cite records in the report — `lookup_attack("pmkid-capture")` gives
  preconditions, tools, mitigation; `lookup_cve(...)` fills the CVE
  column.
- Save every artifact: pcaps, `.22000` files, `call_log()` output,
  WebUI screenshots. The report writes itself off these.
- Include the "how to detect this" side — blue teams read red-team
  reports for defensive value. See § 3.

## Section 3 — blue-team detection labs

The MCP is a red-team tool, but it drives a lot of blue-team work.
Two use patterns:

### 3a — Attack-then-detect

Fire a known attack in the lab, verify your detection catches it.
The MCP is your attack driver; a Kismet / Suricata / Zeek /
commercial WIDS sits on the same RF space and watches.

- **Deauth flood** → detection: `deauth_forensics` corpus,
  `parse_pcap` for the frame histogram, WIDS deauth-rate alert.
- **KARMA active mode** → detection: an AP that responds positively
  to *every* probe request is unphysical; any decent WIDS flags it.
- **Evil twin** → detection: same SSID, different BSSID, different
  IE fingerprint. `beacon_diff` is the pcap-side version of what a
  WIDS does live.
- **PMKID capture** → detection: hcxdumptool's association pattern is
  characteristic; some WIDS fingerprint the client-side sequence.

Recipe pattern:

```python
run_sequence(steps=[
    {"action": "recon_start", "band": "both", "dwell_ms": 250},
    {"action": "wait", "s": 30},
    # …the attack step your blue team is trying to detect…
    {"action": "recon_stop"},
])
# Then correlate `call_log(ssh=True, api=True)` timestamps with the
# blue team's alerts.
```

### 3b — Baseline the RF environment

Before running the attack, capture what "normal" looks like. Then run
the attack and diff.

- `recon_start` + `list_aps` + `list_probe_requests` for 15 minutes
  = the baseline.
- Attack.
- Same recon for 15 minutes = the diff.
- Beacon-side and client-side changes both matter — evil twins are
  visible in the AP list; probe-response fingerprints are in the
  client list.

## Section 4 — home / self-training / bench work

Least legal exposure, most learning per unit time.

### 4a — Setup

Point `Authorization(ssid_allowlist=..., bssid_allowlist=...)` at your
own gear. `i_own_the_airspace` also works if you actually own the
airspace; the allowlist is more precise and gives you the same
refusal-on-typo protection the client-audit path uses. A Faraday
enclosure is nice for repeatability but not required.

### 4b — Skill ladder for a bench

1. **Recon and reading beacons.** `list_aps` → `lookup_ie(48)` to read
   RSN capabilities. Read a lot of them.
2. **Capture and convert.** Own AP, own client, capture a real 4-way
   with the R3 recipe. Learn what a good pcap looks like.
3. **Crack own PSK.** rockyou will find `password12345678` in seconds.
4. **PMKID.** Force your own AP into a PMKID-in-M1 config; capture and
   convert.
5. **Evil twin against your own AP.** Now you know how the WIDS side
   looks.
6. **WPA3 SAE.** Read [`knowledge/wpa3/`](../knowledge/wpa3/); attack
   its transition mode with an own-AP twin.
7. **Enterprise.** hostapd-wpe against a spare AP that supports
   WPA-EAP; MSCHAPv2 → mode 5500. See
   [`knowledge/hostapd-wpe/`](../knowledge/hostapd-wpe/).

### 4c — Bench-to-bag readiness

Before a con or an on-site, run the R1 recon recipe against your
lab AP, capture, convert, crack. If any step surprises you, fix it
before the trip. The lab is the place to hit F1 / F5 / F6 in
[`troubleshooting.md`](troubleshooting.md), not the con.

## Section 5 — DEF CON specifics (update yearly)

**Update note:** This section reflects best-effort knowledge as of the
last edit. Verify against the current year's Wireless Village page
before you fly. If you update this section, update the "last updated"
date below.

- **Last updated:** 2026-08-07 (initial write).
- **Wireless Village page (canonical):** search for "DEF CON Wireless
  Village" in the current year's DEF CON village map. URL changes
  yearly; the DEF CON forums are the fallback if the map hasn't been
  updated.
- **Rules to look for:** deauth policy (broadcast vs. unicast), KARMA
  policy (allowed against village targets only), flag format for the
  year, submission portal URL, points decay per flag.
- **RF environment at DEF CON:**
  - 200+ APs, 3000+ STAs, all within 40 m. Con-floor saturation is
    the RF constant, not a variable.
  - 2.4 GHz is unusable in the main hall by Friday afternoon. Prefer
    5 GHz UNII-1 (channels 36–48) for your rogue APs.
  - 6 GHz is usually clean; the tradeoff is that adapter support is
    still thin in 2026 for monitor+injection.
  - Your antennas matter more than your dBm cap; a 12 dBi panel at
    3 m beats a 30 dBi omni at 30 m in this environment.
  - See [`knowledge/hardware-and-antennas/walkthrough.md § Path A`](../knowledge/hardware-and-antennas/walkthrough.md).
- **Physical positioning:**
  - Wall or corner — bodies attenuate 2.4 GHz, so distance to your
    antenna matters more than dBm.
  - Away from the entrance if you can — foot traffic disrupts
    directional aiming.
- **What has appeared in past years' WCTFs** (illustrative, doesn't
  necessarily repeat):
  - PMKID fastpath against APs with vendor-defaultable PSKs.
  - Hidden-SSID mazes with the reveal in a probe request.
  - Beacon-IE stego in Vendor IEs with recognizable OUIs.
  - WPS-locked routers as a Pixie Dust exercise.
  - Rogue-RADIUS with a specific EAP-PEAP inner target.
  - ANQP-response steganography (Hotspot 2.0).
  - Time-windowed puzzles (flag appears at :00 each hour).

## Deeper docs

- **Where the puzzle lives** — [`wctf_playbook.md`](wctf_playbook.md).
- **Cheat sheet** — [`cheatsheet.md`](cheatsheet.md).
- **Recipes** — [`recipes.md`](recipes.md).
- **When it breaks** — [`troubleshooting.md`](troubleshooting.md).
- **Is my capture good?** — [`handshake_forensics.md`](handshake_forensics.md).
- **Legal** — [`legal_and_consent.md`](legal_and_consent.md).
