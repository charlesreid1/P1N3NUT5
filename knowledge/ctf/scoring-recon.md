# Scoring recon — spot the scoreboard's own probes

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
