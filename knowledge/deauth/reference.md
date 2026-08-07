# Deauth reference

## The frame

The 802.11 Deauthentication frame is management/subtype 12. Wire-format:

```
Byte    Field                       Notes
0-1     Frame Control               subtype 12
2-3     Duration                    NAV
4-9     Address 1 (destination)     broadcast (ff:ff:ff:ff:ff:ff) or STA MAC
10-15   Address 2 (source)          AP BSSID or spoofed
16-21   Address 3 (BSSID)           AP BSSID
22-23   Sequence Control
24-25   Reason Code (2 bytes)       see below
```

Total: 26 bytes. FCS at the tail (4 bytes) is driver-managed.

## Reason codes (802.11-2020 §9.4.1.7)

| code | meaning |
| ---- | ------- |
| 1    | Unspecified reason |
| 2    | Previous authentication no longer valid |
| 3    | Deauthenticated because sending STA is leaving IBSS or ESS |
| 4    | Disassociated due to inactivity |
| 6    | Class 2 frame received from nonauthenticated STA |
| 7    | Class 3 frame received from nonassociated STA |
| 15   | 4-Way Handshake timeout |

Reason 7 is the canonical aireplay-ng deauth reason — it looks like a
legitimate reject from the AP, so clients reassociate quickly.

## PMF interaction

Under 802.11w PMF (802.11-2020 §11.34):

- **PMF-required** (MFPR=1) — broadcast deauth is not accepted;
  unicast deauth between PMF-negotiated peers is authenticated.
- **PMF-optional** (MFPC=1, MFPR=0) — PMF-capable clients drop
  unauthenticated deauths; PMF-disabled clients (transition-mode
  legacy) still accept them.
- **PMF-disabled** — anyone can deauth anyone.

## Tools

- `aireplay-ng -0 <count> -a <bssid> [-c <client>] <iface>` — the classic
- `mdk4 <iface> d -B <bssid>` — mdk4 mode d
- Scapy: `Dot11(type=0, subtype=12, addr1=..., addr2=..., addr3=...) /
  Dot11Deauth(reason=7)`

## Cite

- IEEE Std 802.11-2020, §9.3.3.13 (Deauthentication), §9.4.1.7
  (Reason Code field), §11.34 (Protected Management Frames).
- aircrack-ng documentation — aireplay-ng deauthentication.
