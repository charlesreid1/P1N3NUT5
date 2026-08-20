# hcxtools — the modern handshake + PMKID toolchain

Author: ZerBea. Supplanted aircrack-ng for WPA2/3 handshake capture
and PMKID capture. Three tools we use:

- **`hcxdumptool`** — captures 802.11 frames straight from a monitor
  interface (or, more accurately, manages its own monitor mode).
  BPF-based filtering by BSSID / ESSID.
- **`hcxpcapngtool`** — converts a pcap/pcapng to hashcat mode 22000
  input (WPA*01 for PMKID, WPA*02 for 4-way handshake).
- **`hcxlabtool`** — aggressive-capture mode; runs hcxdumptool in a
  loop with sweep patterns for lab use.

> **Version pin.** This page is written against **hcxdumptool 7.3**
> (2024-Q4 stable). Older tutorials on the web target the 4.x/5.x
> CLI, which was reworked in 6.x and again in 7.x. Use the compat
> table below when reading stale write-ups.

## Compat table — 4.x → 6.x → 7.x flag transitions

| Old flag (4.x/5.x)          | New flag (6.x / 7.x)        | Notes                                                        |
|-----------------------------|-----------------------------|--------------------------------------------------------------|
| `-o <file>`                 | `-w <file>`                 | Output pcapng. Renamed in 6.x.                               |
| `--filterlist_ap=<file>`    | `--bpf=<bpf_file>`          | Filter by BSSID/ESSID now goes through a BPF program (6.3+). |
| `--filtermode=<n>`          | *(removed)*                 | Filter direction is encoded in the BPF program itself.       |
| `--enable_status=<n>`       | `--enable_status=<n>`       | Still present; prints status lines to stdout. No TUI exists. |
| `--rds=<n>`                 | *(removed)*                 | Gone in 6.2. Use `--enable_status` if you want status lines. |
| `--use_gpsd=1`              | `--gpsd`                    | Renamed and now a boolean flag (no `=1`).                    |
| Internal active deauth      | *(removed)*                 | 6.x dropped all active attack modes. Chain mdk4 / aireplay-ng / scapy externally to force reassoc. |
| `--rcascan=1`               | `--rcascan=<active\|passive>` | Scan mode value changed from int to enum.                   |
| `--do_rcascan`              | `--rcascan=active`          | Renamed.                                                     |

Sources: `hcxdumptool --help` on 7.3; ZerBea CHANGELOG entries for
6.0, 6.2, 6.3, and 7.0.

## `hcxdumptool` (7.3 CLI)

```
# Capture everything on channel 6.
hcxdumptool -i wlan1 -w /tmp/cap.pcapng -c 6 --enable_status=3

# Filter to specific target BSSIDs via a BPF program.
#   1. Write a BPF source that matches your targets:
#      echo 'wlan addr3 aa:bb:cc:dd:ee:ff' > /tmp/target.bpf.src
#   2. Compile it against the radiotap linktype:
#      tcpdump -y IEEE802_11_RADIO -F /tmp/target.bpf.src -ddd \
#              > /tmp/target.bpf
#   3. Point hcxdumptool at the compiled program:
hcxdumptool -i wlan1 -w /tmp/cap.pcapng -c 6 --bpf=/tmp/target.bpf
```

`--enable_status=<n>` prints status lines to stdout (there is no
interactive TUI); use a bitmask value like `3` or `15` to raise
verbosity. Drop it entirely for scripted / headless captures.

> **Active deauth is no longer built in.** 6.x removed every active
> attack mode from hcxdumptool. If you need to force a reassociation
> for a 4-way capture, run `mdk4 d`, `aireplay-ng -0`, or a scapy
> deauth in a second process on the same monitor iface.

## `hcxpcapngtool`

```
# Extract all hashcat 22000 lines
hcxpcapngtool -o /tmp/hs.22000 /tmp/cap.pcapng

# Enumerate what the pcap contains (BSSIDs, clients, handshake pairs)
hcxpcapngtool --info /tmp/cap.pcapng

# Filter output to a specific ESSID
hcxpcapngtool -o /tmp/hs.22000 --essid_regex '^UPC[0-9]{7}$' /tmp/cap.pcapng

# Aggressive conversion tuning
hcxpcapngtool \
  -o /tmp/hs.22000 \
  --all \                   # emit every 4-way/PMKID even if incomplete pairs
  -E /tmp/essids.txt \      # dump every ESSID seen (for wordlist gen)
  --ignore-ie-order \       # accept M2 even if the RSN IE order was
                            # rearranged by the client (some Realtek chips)
  --pmkid-client-only \     # only extract PMKIDs sourced from the STA's
                            # M2, not AP's M1 — reduces false-positive
                            # cracks when APs cache stale PMKIDs
  /tmp/cap.pcapng
```

Also see `pcap/walkthrough.md` for the `.pcap ↔ .pcapng` conversion
recipe (`editcap`, `tshark -F pcapng`).

## The 22000 line format

Reproduced from `hashcat/reference.md`:

```
WPA*<type>*<PMKID/MIC>*<AP_MAC>*<STA_MAC>*<ESSID hex>*<ANonce>*<EAPOL frame>*<MC>
```

- `type=01` — PMKID (only M1 needed)
- `type=02` — EAPOL 4-way (M2 present)

## Entering monitor mode — the two canonical paths

Every capture in the corpus assumes a monitor iface. Two ways to get
one. Do the `airmon-ng check kill` (or explicit `systemctl stop`)
step first either way — the userland stack fights monitor mode.

```
# Path A — airmon-ng (renames interface, kills interfering processes)
sudo airmon-ng check kill
sudo airmon-ng start wlan1
# Now wlan1mon exists.

# Path B — plain iw (keeps original name, no interference kill)
sudo systemctl stop NetworkManager wpa_supplicant iwd
sudo ip link set wlan1 down
sudo iw dev wlan1 set monitor none
sudo ip link set wlan1 up
# wlan1 is now monitor. Set channel:
sudo iw dev wlan1 set channel 6
```

Path A renames the iface (`wlan1` → `wlan1mon`) and does the
process-kill for you; scripts and tooling that hard-code `wlan1mon`
prefer it. Path B keeps the original name (matters for `hostapd`
configs that reference `wlan1` verbatim) and is faster to script,
but you must stop the daemons yourself.

## Canonical channel lists

Handy when passing `-c` to `airodump-ng`, `--channel_list=` to
`hcxdumptool`, or picking a `channel=` for hostapd:

```
# 2.4 GHz all
1,2,3,4,5,6,7,8,9,10,11        # US
1,2,3,4,5,6,7,8,9,10,11,12,13  # EU / most-of-world
# US only allows 12/13 for STA/passive scan, not AP TX

# 5 GHz UNII-1 (no DFS, always safe)
36,40,44,48

# 5 GHz UNII-3 (no DFS, higher power OK)
149,153,157,161,165

# 6 GHz PSCs (only every 4th channel — the 15 canonical scan chans)
5,21,37,53,69,85,101,117,133,149,165,181,197,213,229

# Combined 2.4 + UNII-1 capture list
1,6,11,36,40,44,48
```

DFS band (52-144) is intentionally omitted — the 60 s CAC dwell
makes it useless for rogue APs and ambient enough for capture that
you'd normally hop it separately.

## Cite

- ZerBea hcxdumptool GitHub.
- Steube 2018 PMKID advisory.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`.
