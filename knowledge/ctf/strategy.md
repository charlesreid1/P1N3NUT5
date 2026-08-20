# First 60 seconds — how to rank targets

You just landed in a WCTF room. The Pineapple is up, recon is
running, `list_aps()` returns 30 APs. Which one is the puzzle?

## The likelihood order (highest → lowest)

1. **WPS is on.** Look at the WPS IE in every beacon. A beacon
   advertising `WPS State = configured, unlocked` on a router with a
   known-Pixie-vulnerable manufacturer string is the fastest lane.
2. **PMKID leaks.** APs whose M1 carries a non-zero PMKID field.
   The path is: `capture_pmkid` → `convert_to_hashcat(mode=22000)` →
   `crack_start(rockyou.txt)`. Client-free.
3. **Vendor default SSID.** SSID matches `/^UPC\d{7}$/`,
   `SpeedTouch……`, `BTHub…-…`, `SKY…-…`. Run the derivation, get
   candidate PSK(s), validate offline. No radio time.
4. **WPA3 transition mode.** RSN IE carries both AKM 2 (PSK) and
   AKM 8 (SAE). Downgrade a WPA2 client, capture, crack.
5. **PMF off.** Deauth is unrestricted. A live-client + targeted
   deauth gets you a 4-way handshake fast.
6. **Enterprise (WPA-EAP) with weak cert validation.** Rogue-RADIUS
   + inner-EAP downgrade harvests MSCHAPv2 → hashcat 5500.
7. **Exotic IE.** A Vendor-Specific IE with an unfamiliar OUI or a
   Venue Info string with human-readable content. Beacon-IE stego —
   the flag is embedded in the IEs themselves; no crack needed.
8. **Everything else.** Full WPA3-SAE with PMF-required and no
   transition mode. Reach for Dragonblood if the SAE impl is weak,
   or pivot to a captive-portal / rogue-RADIUS engagement side of
   the room.

## What NOT to reach for first

- Broadcast deauth flooding — noisy, and PMF-required APs no-op it.
- WEP crack on a WPA2-PSK AP because you saw the "Privacy" bit set.
  Read the RSN IE, not just capabilities.
- KRACK / Kr00k / FragAttacks — precondition-heavy. Only after
  fingerprinting the client chipset.

## Two-op recon/attack split

If you have two operators: **op 1 runs `run_sequence` recon +
`list_aps` + `list_probe_requests` continuously; op 2 attacks the
top target from the ranked list.** The recon loop keeps updating
which targets are alive and which clients are still probing.

## Time budget — per target

Cap wall-clock spend so a single bad target can't sink the run:

| Phase                        | Budget          | Then                                    |
| ---------------------------- | --------------- | --------------------------------------- |
| Triage (recon + fingerprint) | 20 min          | If still unclear, drop → next target    |
| Capture attempt (live radio) | 45 min          | If no PMKID + no 4-way, drop            |
| Offline crack (rockyou)      | 30 min          | If <50% dict-in and no hits, queue      |
| Hard cap (any target)        | 90 min total    | Unless offline crack ≥ 50% wordlist-in  |

The 90-minute cap is the abandonment trigger unless the offline crack
is already deep in the wordlist — burning through the last 50% of
rockyou for a probable no-hit is worse than shifting to a fresh target.

## Abandonment triggers — hard "skip"

- **PMF-required + no clients associating.** No PMKID, no 4-way, no
  Kr00k victim. Deauth won't land. Skip; check for a WPA3-transition
  side elsewhere in the room.
- **WPA3-SAE only with H2E-only bit set (RSN Ext IE bit).** No
  Dragonblood side-channel, no PMKID, no downgrade. Skip unless a
  cert-phish path opens.
- **Passphrase not in rockyou + best64 after 30 min.** Queue for a
  bigger overnight run (weakpass_3a / hashesorg2019); do not sit on
  the target. Move to the next.
- **All beacons show `AP Setup Locked=1` with no `Locked=0` window
  in 5 min of watching.** WPS is not a path.
- **Enterprise + strong cert pinning observed** (client refuses
  rogue-RADIUS after 2 min). Skip unless another EAP method is on
  offer.

## Overnight queue

Anything worth queueing (deep wordlist runs, Dragonblood collection,
long ANQP dwells) goes on the operator's laptop, not the Pineapple.
Note the target, the artifact path, and what "success" looks like so
someone else can pick it up.

## Cite

- Every ranked category has an `attacks.json` id — cross-reference
  the record for preconditions before firing.
