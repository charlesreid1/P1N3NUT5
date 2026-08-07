# SSID Confusion recognition

The point of the attack (Vanhoef & Yseboodt 2024, CVE-2023-52424) is
that it's *not* detectable the way an evil twin is. The SSID is not
authenticated in the 4-way handshake, so a client can be steered
between two legitimate SSIDs (both known to it, both with valid
credentials on either side) without generating any of the anomalies
a WIDS looks for.

## What a WIDS sees — nothing useful

A conventional evil-twin WIDS rule fires on:

- Duplicate SSID on a channel where the "real" AP isn't broadcasting.
- BSSID mismatch for a known SSID.
- Beacon-interval / DTIM / vendor-IE anomalies vs the whitelisted AP.

SSID Confusion generates none of these. Both networks are real; the
attacker doesn't need to spoof BSSIDs, clone beacons, or lie about
capabilities. The client's association is authentic on the network
it lands on — it just *believes* it's on the other one.

## What you can actually observe

Passive signals, all of them subtle:

1. **Two APs the target trusts, both in range, both configured with
   PSKs the target has.** The attacker is either the operator of one
   of them or has arranged the physical layout to swap the target
   between the two. Presence of both networks in the target's known
   list is the precondition.
2. **Client behavior post-association that doesn't match its expected
   trust posture.** For example, a VPN configured to auto-connect on
   SSID `Corp-WiFi` doesn't fire because the client is actually on
   `Corp-Guest`. If you're the CTF operator watching a target STA's
   traffic and its VPN never comes up on the "trusted" SSID, that's
   the smell.
3. **The 4-way handshake completes but subsequent RSN IE cross-check
   fails silently.** Some patched clients (Windows 11 24H2+, iOS 17.4+)
   log a warning; unpatched clients (older Linux with wpa_supplicant
   <2.11, unpatched iwd, most embedded stacks) don't.

## Patched vs unpatched clients (2026)

Client-side mitigation (Beacon Protection + SSID-in-4-way binding)
rolled out unevenly:

- **Patched by default 2024–2025:** Windows 11 24H2, iOS 17.4+,
  Android 15+, Fedora/Ubuntu wpa_supplicant 2.11+, current iwd.
- **Vulnerable on default configs:** older Linux distros (wpa_supplicant
  2.9–2.10 unless backported), many embedded stacks, most IoT
  clients, some enterprise supplicants shipped pre-2024.

## Confirming a target is vulnerable

Two-step probe (attacker-side):

1. Set up two APs with the two SSIDs the target trusts (or use two
   real cooperating APs). Use identical PSK on both intentionally
   for the demo; production attack uses distinct PSKs on legitimate
   networks the target has creds for.
2. Force a roam. If the client transitions between them without
   surfacing a UI warning and without a Beacon Protection MIC
   failure, it's vulnerable.

## In a pcap

Filter Beacon Protection IE (Element ID 92, "Beacon Timing" —
distinct from the older ID also numbered 92; check the specific IE
ID from `ies.json`). Presence of a `Beacon Protection Key ID` IE and
`MME` (Management MIC Element) on a beacon indicates the AP is
running beacon-side mitigation. Absence = downstream clients get no
help.

## The CTF pattern

An SSID-confusion puzzle typically presents:

- Two APs both known to a target STA (given as part of the puzzle).
- A "target flag" that is what the client sends when it believes it's
  on network X but is actually on Y (an auto-provisioned bearer
  token, an intranet request, etc.).

You force the confusion, sniff, extract the payload the client leaked
under the wrong trust context.

## Cite

- Vanhoef & Yseboodt 2024 — SSID Confusion, USENIX Security 2024.
- CVE-2023-52424.
- knowledge/ssid-confusion/reference.md.
- attacks.json: `ssid-confusion-cve-2023-52424`.
