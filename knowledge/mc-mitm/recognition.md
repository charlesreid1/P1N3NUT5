# Multi-Channel MitM recognition

MC-MitM is the primitive KRACK is built on: interpose on a client
between the AP's actual channel and a rogue channel by cloning the
BSSID and running the same SSID on two channels simultaneously. On
the Mark VII this is a natural fit for the dual-radio hardware.

## In a pcap — the fingerprint

You are looking at the *result* of an MC-MitM setup: two frames from
the same claimed BSSID on two different channels within a short
window. Load the capture, filter `wlan.bssid == <target>` and group
by radiotap channel:

- Legit AP: single channel, monotonic sequence numbers.
- MC-MitM: two channels see beacons from the "same" BSSID within
  seconds of each other. The seq-num streams diverge — each rogue
  radio maintains its own counter.

Wireshark: `radiotap.channel.freq` split view. Two channels for a
single BSSID during the same time window is diagnostic.

## Signal-strength triangulation

The real AP is at a fixed location; the rogue radios are on the
attacker's hardware. Two beacons claiming the same BSSID but with
different RSSI patterns as you walk the venue → one of them is the
attacker. On the Pineapple, sample from the second radio while the
first floods the target channel; RSSI stability differences show up
in a few seconds of pacing.

## Client-side symptoms

An MC-MitM'd client:

- Roams to the rogue radio and back rapidly (each side alternates
  winning the STA).
- Has a `wlan.fc.retry` rate elevated on frames destined for the
  claimed AP (because two APs racing to answer creates collisions
  the STA sees as retries).
- May generate 802.11k Neighbor Report Response asking about the
  duplicate channel — a well-configured STA notices the anomaly.

## Distinguishing from a plain evil twin

Evil twin: clone SSID+BSSID+channel, one channel only, force
reassoc.

MC-MitM: clone SSID+BSSID on **two** channels, sit between them.

The critical tell is *two channels for one BSSID*. An evil twin
never does this.

## When you'd use it

- The target AP has PMF-required. Deauth is off the table.
- The target client supports 802.11k/v and can be steered between
  bands (5 → 2.4 GHz).
- You need to interpose during the 4-way handshake to run a
  KRACK-family key-reinstall — MC-MitM is how the KRACK PoC gets a
  M3 to a client twice.

## Confirming your own setup is working

Pineapple side, from SSH:

```
iw dev wlan0 info   # should show channel 6 (real AP mirror)
iw dev wlan1 info   # should show channel 36 (rogue channel)
```

Both interfaces should show `type AP` with the same SSID + BSSID.
`tcpdump -i wlan0mon -e -c 5 type mgt subtype beacon` and same on
`wlan1mon` — the target BSSID should appear on both.

## Cite

- Vanhoef & Piessens 2017 — KRACK (uses MC-MitM as the setup primitive).
- knowledge/mc-mitm/reference.md.
- knowledge/pineapple-mk7/reference.md (dual-radio hardware section).
- attacks.json: `mc-mitm-dual-radio`.
