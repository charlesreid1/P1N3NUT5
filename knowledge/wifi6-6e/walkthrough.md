# Wi-Fi 6 / 6E — walkthrough

Three practical primitives against 6/6E gear. All three assume a
Pineapple Mk VII plus a `wlan1` capable of 5 GHz monitor+injection. 6 GHz
tuning is optional; the RNR path deliberately does not need it.

## Path A — RNR-driven 6 GHz recon (no 6 GHz radio)

A 6E-capable AP MUST advertise its 6 GHz BSSIDs in the Reduced Neighbor
Report IE of its 2.4/5 GHz beacons. That means you can enumerate 6 GHz
targets from a stock 2.4/5 GHz card.

```
# 1. Passive capture on 2.4 + 5 GHz.
airodump-ng --band abg -w /tmp/rnr wlan1mon

# 2. Extract RNR IEs (IE 201) from beacons.
tshark -r /tmp/rnr-01.cap -Y "wlan.tag.number == 201" \
       -T fields -e wlan.bssid -e wlan.rnr.tbtt_info.bssid \
                 -e wlan.rnr.tbtt_info.channel
```

Each RNR entry names a neighbor BSSID + operating class + channel. If
the channel is in the 6 GHz range (operating class 131–137), you have a
6 GHz target enumerated from 2.4/5 GHz probing alone.

## Path B — TWT forced-sleep abuse

TWT (Target Wake Time) is negotiated with Action frames. A spoofed TWT
Setup Request from the AP's BSSID can shove a client into extended
sleep — the client won't hear anything until the wake window it
believes it agreed to.

```python
# scapy sketch (needs a monitor+inject iface)
from scapy.all import *
# TWT Setup frame — Category 6 (S1G/HE), Action 4 (TWT Setup)
# with a fabricated Target Wake Time element requesting a
# very long wake interval (e.g. 4.29 s = 2^32 microseconds).
twt = Dot11(
    type=0, subtype=13,           # mgmt, action
    addr1=CLIENT_MAC,
    addr2=AP_BSSID,               # spoofed
    addr3=AP_BSSID,
) / Raw(load=bytes.fromhex(
    "06"      # category HE
    "04"      # action TWT Setup
    "..."     # TWT element with long wake interval
))
sendp(RadioTap()/twt, iface="wlan1mon")
```

While the client sleeps, you can stand up a rogue on the same SSID+PSK
and take over the association on wake. This is a client-side DoS
primitive; combine with evil-twin for takeover.

## Path C — RU-based OFDMA DoS

Trigger frames instruct STAs when to transmit on which Resource Units.
An attacker who acknowledges an RU allocation but never transmits eats
capacity for other STAs. Not a client-takeover primitive but useful to
degrade a target AP so a rogue-side reassociation looks attractive.

## Path D — 6 GHz auth reduces to Dragonblood-family

Any auth attack on 6 GHz is a WPA3-SAE attack (no WPA2 allowed on
6 GHz). If the client tolerates a WPA2 side on 2.4/5 GHz for the same
network (which many corporate deployments do), the whole 6 GHz
"WPA3-only" property doesn't help you — pivot to the 2.4/5 GHz side
and treat it as WPA2/3 transition. See `wpa3-transition-downgrade`.

## Failure modes

- **RNR IE absent.** Cheaper 6E APs sometimes omit RNR from their
  5 GHz beacons even though the spec says MUST. Fall back to a 6 GHz
  card if you have one (ath11k / mt76 / rtw89 with a 6E-capable module).
- **TWT frame ignored.** Client isn't HE-capable, or its supplicant
  requires TWT to be pre-negotiated with a valid handshake. Confirm
  the client actually negotiated TWT with a prior `wireshark`
  filter `wlan.fixed.category_code == 6`.
- **6 GHz-only client.** Some laptops with 6E cards will refuse to
  associate to a 2.4/5 GHz WPA2 side even when it advertises the same
  SSID + PSK. The downgrade path stops there.

## Cite

- IEEE Std 802.11ax-2021, §26 (HE), §27 (TWT).
- Wi-Fi Alliance — Wi-Fi CERTIFIED 6E requirements.
- attacks.json: `rnr-6ghz-enumeration`, `twt-forced-sleep-abuse`,
  `ru-based-ofdma-dos`, `wpa3-transition-downgrade`.
