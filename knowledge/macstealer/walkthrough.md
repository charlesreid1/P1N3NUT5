# MacStealer walkthrough

You are on the target network with the PSK (or the network is Open / OWE).
You know the victim's MAC. You want the AP's next queued return-traffic
frame for the victim to arrive at your STA.

## Setup

Two interfaces on the attacker box (the Pineapple works if it has two
radios; a laptop with the built-in and an Alfa AWUS036ACHM works too):

- `wlan0` — associated to the target AP as a legitimate STA under the
  attacker's real MAC. This is your baseline.
- `wlan1` — monitor mode, watching the victim + AP conversation. You
  use this to detect the disassoc event and to time the reassociation.

Baseline association:

```
# Associate to the target network as yourself.
wpa_passphrase TargetSSID SharedPassword123 > /tmp/tgt.conf
wpa_supplicant -B -i wlan0 -c /tmp/tgt.conf
dhclient wlan0
```

Sniffer on the target's channel:

```
# Verify channel first via `iw wlan1 scan | grep -A5 TargetSSID`.
airmon-ng start wlan1 6
airodump-ng --bssid <AP-BSSID> -c 6 wlan1mon
```

## Steps

1. **Wait for the victim to disassociate** — natural disconnect, sleep-
   induced disassoc, or attacker-forced deauth. `aireplay-ng` has no
   `--disassoc` flag; use `aireplay-ng -0 1 -a <ap-bssid> -c <victim-mac>
   wlan1mon` for a targeted deauth, or `mdk4 wlan1mon d -B <ap-bssid>
   -c <chan>` / a scapy Dot11Disas frame for a true disassoc. Note the
   moment.
2. **Change your STA's MAC to the victim's** while the AP still has the
   victim's association state cached but before the AP's own idle-timeout
   sweeps it. Timing window is per-vendor — Vanhoef's paper reports 3-30
   seconds on affected APs.
   ```
   ip link set wlan0 down
   ip link set wlan0 address <victim-mac>
   ip link set wlan0 up
   ```
3. **Reassociate under the borrowed MAC.** Same wpa_supplicant conf, the
   MAC change alone is enough:
   ```
   wpa_supplicant -B -i wlan0 -c /tmp/tgt.conf
   dhclient wlan0
   ```
   Complete the 4-way handshake as usual.
4. **Capture the queued return traffic.** Any packet the AP had queued
   for the victim's MAC now arrives at your STA. Watch `tcpdump -ni
   wlan0` for what lands. WCTF flags typically live in DNS lookups the
   client hadn't finished, HTTP responses the client had requested, or
   in a mail sync payload the client hadn't received yet.

## Failure modes

- **AP patched.** The MacStealer paper's mitigation table shows Linux
  mac80211 6.1+ and hostapd 2.11+ bind the association state to the
  crypto session, not the MAC. Reassociation from a new SNonce drops
  queued frames for the previous session. Nothing arrives.
- **Timing window closed.** The AP's idle-timeout on the previous
  association fired before your MAC change. You associated cleanly under
  the borrowed MAC, but no queued frames remain to intercept.
- **Client isolation on a shared AP.** If the AP enforces client
  isolation and does it correctly (session-keyed, not MAC-keyed), the
  primitive still lands but the traffic you receive is only what the AP
  itself was routing to that MAC — no LAN-lateral gain.
- **PMF-required doesn't help.** MacStealer is a data-plane primitive
  post-association; PMF protects management frames, not the ambiguity of
  which STA a queued Data frame belongs to.

## WCTF flag shape

DEFCON WCTF 2024+ has used MacStealer as a puzzle where the flag lands
in the *tail* of a legitimate client's session — a DNS response for
`flag-<n>.wctf.example` that the client had requested but not yet
received when it disassociated. You get one shot per disassoc; time it
right and the response frame drops into your `tcpdump`. Miss and you get
nothing until the next disconnect cycle.

Composing with SSID Confusion: some 2026 puzzle designs pair the two.
SSID Confusion gets the attacker on the network without a real PSK
(shared-PSK trick); MacStealer then hijacks the intra-network traffic
once inside.

## Cite

- Vanhoef, "MacStealer" (BlackHat Asia 2023).
- CVE-2022-47521 — MacStealer (Linux mac80211 post-disassoc queue).
- CVE-2022-47522 — companion Framing Frames power-save queue tap.
- `attacks.json: macstealer-mac-hijack`.
- `ssid-confusion/` — the companion attack on the same 4-way binding gap.
