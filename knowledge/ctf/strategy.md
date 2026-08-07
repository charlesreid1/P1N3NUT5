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

## Cite

- Every ranked category has an `attacks.json` id — cross-reference
  the record for preconditions before firing.
