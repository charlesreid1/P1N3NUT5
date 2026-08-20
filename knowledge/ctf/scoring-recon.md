> **Status: template — confirm at the on-site briefing.** The details
> below (portal URL, flag regex, blackout windows, submission
> gotchas) are best guesses from prior years and community write-ups.
> The Village staff hand out the *actual* values at opening. Overwrite
> this file with the current-year specifics before relying on it.

## DEF CON Wireless Village — WCTF specifics

- **Portal URL pattern.** Historically the Village has run either a
  self-hosted CTFd (`https://ctf.wctf.wirelessvillage.ninja/` or a
  yearly subdomain) or, in older years, a `ctftime.org`-linked
  scoreboard. Confirm the current-year URL at the Village desk.
- **Flag regex.** Default assumption:
  `flag\{[A-Za-z0-9_\-]+\}` (case-sensitive). Some challenges use
  a vendor-specific `wctf\{...\}` or `dc\d+\{...\}` variant. If in
  doubt, submit both cases.
- **Blackout windows.** No submissions accepted during opening
  ceremony (Fri ~10:00 Vegas time), closing/awards (Sun ~14:00), or
  any explicitly announced maintenance pause. Save flags locally and
  submit when the portal reopens.
- **Submission caveats.**
  - Some challenges accept the **SHA1 of a captured artifact**
    (pcap, key hex, IE payload) rather than the plaintext — the
    challenge text will name the artifact and the digest algorithm.
  - Team submissions rate-limit ~1/sec; batch by hand if you have a
    stack of small flags.
  - Duplicate submissions do not count; if the flag lives on two
    puzzles, submit under the canonical challenge ID.

# Scoring recon — spot the scoreboard's own probes

**Verified against:** P1N3NUT5 knowledge corpus as of 2026-Q3

## DEF CON Wireless Village (WCTF) submission surface

- **Scoreboard portal.** Confirm at the on-site briefing;
  historically hosted at a Village-specific URL on the con network
  (e.g., a CTFd instance served over the WCTF SSID). Check the
  Wireless Village Discord / printed handouts for the current URL —
  it changes year to year.
- **Flag regex.** WCTF has historically used both
  `flag\{[A-Za-z0-9_-]+\}` and vendor-specific formats
  (`WCTF{...}`, `PineappleGang{...}`, hex-only artifacts). Some
  challenges accept the SHA-1 of a captured artifact rather than a
  plaintext string — read the challenge description carefully.
- **Blackout windows.** No submissions during opening ceremony
  (typically Fri 10:00–11:00 PT) or the awards session (Sun
  ~13:00 PT). Bots may still respond during these windows; treat
  timestamps as your own guide.
- **Rate-limit / anti-abuse.** Submission endpoints typically
  rate-limit at 3–5 attempts/minute per team; brute-forcing flag
  strings will lock you out.

Confirm the current-year specifics at the on-site Village briefing.
This file is a template — the exact URLs and blackout hours change
each year.


WCTF scoring bots ping their own flag traps to verify uptime. If you
can identify a scorer, you can pin down which APs are targets vs.
decoys. Also: some puzzles only surface a flag in specific time
windows — recon the timing.

## Recognition

A scorer's client looks different from a real WCTF attendee's client:

- **Highly regular probe / association timing** (every 30 s, every
  minute).
- **A stable OUI** across all sightings — no MAC randomization.
- **Association attempts to specific target BSSIDs** and never to
  general-population APs.
- **Uniform frame types** — always probe, association, one small
  data exchange, disassoc. No real user behavior.

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "abg", "dwell_ms": 250},
    {"action": "wait", "s": 900},           # 15-minute passive baseline
    {"action": "recon_stop"},

    # 1. List candidate scorers — clients whose activity is
    #    periodic and OUI is scanner-associated.
    {"action": "list_periodic_clients",
     "period_tolerance_s": 5,
     "min_hits": 5},

    # 2. For each candidate, list the BSSIDs they associated to.
    {"action": "list_scorer_targets",
     "client_macs": ["<candidate-mac>", "..."]},
])
```

## MCP mapping / fallback

`list_periodic_clients` and `list_scorer_targets` are **not in `src/`**.
Approximate them with periodicity analysis over `list_clients` and
`list_associations` snapshots, or drive from a raw pcap with tshark.

**Fallback shell chain — periodic-client detection:**

```bash
# 1. capture a long baseline
sudo tcpdump -i wlan1mon -w /tmp/baseline.pcap &
sleep 900
sudo pkill tcpdump

# 2. per-client probe cadence
tshark -r /tmp/baseline.pcap \
    -Y "wlan.fc.type_subtype == 0x04" \
    -T fields -e frame.time_epoch -e wlan.sa \
  | awk '{ print $2, $1 }' \
  | sort \
  | awk 'prev_mac==$1 { dt=$2-prev_t; print $1, dt } { prev_mac=$1; prev_t=$2 }' \
  | sort -k1,1 -k2,2n

# 3. flag any client whose intervals cluster around 30/60/300 seconds
#    with < 5s stddev — that's a likely scorebot.
```

## The insight — target vs. decoy

If out of 30 APs in the room, exactly 5 receive periodic association
attempts from a scorer client, those 5 are the *real* puzzle APs.
The other 25 are decoys.

## Time-based puzzles

Some WCTF flags only appear at specific times — a beacon-stego
payload that rotates every 5 minutes, a captive portal that only
serves the flag between :00 and :01 of each hour, an ANQP element
that changes every 30 s.

Detection:

- **Beacon Vendor-IE content diff over time.** Sample the beacon at
  30 s intervals; a changing payload is the tell.
- **DTIM period pattern** — some puzzles encode data in the DTIM
  interval variation.
- **Association behavior of the scorer** correlates with when the
  flag is "live."

## Failure modes

- **Scorer randomizes its MAC.** Rare — most scoring infra doesn't
  bother. If it does, use `client_fingerprints.json` heuristics.
- **Scorer runs on wired.** Then it doesn't emit RF signals. Recon
  won't find it. Watch the AP-side traffic (once you have a foothold
  in one AP) for periodic wired connections.
- **Multiple scorers.** Filter by the specific target set each
  scorer touches — different scorers cover different flags.

## Cite

- attacks.json: `pineap-passive-probe-log`.
- SensePost 2014 — passive client analysis.
- Snoopy (paper reference in bibliography if present).
