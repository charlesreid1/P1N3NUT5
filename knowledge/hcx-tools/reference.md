# hcxtools — the modern handshake + PMKID toolchain

Author: ZerBea. Supplanted aircrack-ng for WPA2/3 handshake capture
and PMKID capture. Three tools we use:

- **`hcxdumptool`** — captures 802.11 frames straight from a monitor
  interface (or, more accurately, manages its own monitor mode).
  Aggressive filtering by BSSID / ESSID.
- **`hcxpcapngtool`** — converts a pcap/pcapng to hashcat mode 22000
  input (WPA*01 for PMKID, WPA*02 for 4-way handshake).
- **`hcxlabtool`** — aggressive-capture mode; runs hcxdumptool in a
  loop with sweep patterns for lab use.

## `hcxdumptool`

```
# Capture everything on channel 6 for 60s
hcxdumptool -i wlan1 -o /tmp/cap.pcapng --enable_status=1 -c 6

# Filter to specific target BSSIDs
hcxdumptool -i wlan1 -o /tmp/cap.pcapng --enable_status=1 \
            --filterlist_ap=/tmp/target.list --filtermode=2

# The filter list is one BSSID per line, colons or bare hex both OK.
```

The `--enable_status=1` flag turns on the real-time TUI status
display — handy when running interactively; drop it for scripted
use.

## `hcxpcapngtool`

```
# Extract all hashcat 22000 lines
hcxpcapngtool -o /tmp/hs.22000 /tmp/cap.pcapng

# Enumerate what the pcap contains (BSSIDs, clients, handshake pairs)
hcxpcapngtool --info /tmp/cap.pcapng

# Filter output to a specific ESSID
hcxpcapngtool -o /tmp/hs.22000 --essid_regex '^UPC[0-9]{7}$' /tmp/cap.pcapng
```

## The 22000 line format

Reproduced from `hashcat/reference.md`:

```
WPA*<type>*<PMKID/MIC>*<AP_MAC>*<STA_MAC>*<ESSID hex>*<ANonce>*<EAPOL frame>*<MC>
```

- `type=01` — PMKID (only M1 needed)
- `type=02` — EAPOL 4-way (M2 present)

## Cite

- ZerBea hcxdumptool GitHub.
- Steube 2018 PMKID advisory.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`.
