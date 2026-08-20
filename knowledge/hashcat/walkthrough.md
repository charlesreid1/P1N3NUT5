# hashcat — walkthrough

Baseline dictionary → rule stacking → mask attack → hybrid. In that
order for a WCTF-scale PSK: the corpus of DEF CON WCTF PSKs is
mostly rockyou + best64 with occasional theme-derived candidates.

## Preconditions

- `.22000` file emitted by `hcxpcapngtool`. See `pmkid/walkthrough.md`
  or `4-way-handshake/walkthrough.md`.
- GPU host with recent hashcat (>= 6.2). Pineapple itself is CPU-only
  and unrealistic for anything past a small mask.

## Baseline dictionary

```
hashcat -m 22000 hs.22000 /path/to/rockyou.txt -w 4 --status --status-timer=5
```

Expect this to finish in seconds if the PSK is in rockyou.

## Rule stacking (best64, d3ad0ne, OneRule)

Multiplies the wordlist by transforming each candidate:

```
hashcat -m 22000 hs.22000 rockyou.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 22000 hs.22000 rockyou.txt -r rules/d3ad0ne.rule
hashcat -m 22000 hs.22000 rockyou.txt -r rules/OneRuleToRuleThemAll.rule
```

`OneRuleToRuleThemAll` is the current community-standard heavy pass.
Runtime scales with rule count × wordlist size.

## Mask attack — structure known

Common structures:

```
# 8 digits (default WPS-derived PSKs, some ISPs)
hashcat -m 22000 hs.22000 -a 3 ?d?d?d?d?d?d?d?d

# lower + 4 digits at the end (very common home PSK)
hashcat -m 22000 hs.22000 -a 3 ?l?l?l?l?l?l?d?d?d?d

# 10 chars, mix
hashcat -m 22000 hs.22000 -a 3 -1 ?l?d ?1?1?1?1?1?1?1?1?1?1
```

## Hybrid — wordlist + mask suffix / prefix

```
# suffix — wordlist then digits (Password2024)
hashcat -m 22000 hs.22000 -a 6 wordlist.txt ?d?d?d?d

# prefix — digits then wordlist
hashcat -m 22000 hs.22000 -a 7 ?d?d?d?d wordlist.txt
```

## SSID-derived wordlist

```
# cewl the venue's website
cewl -d 2 -w /tmp/site.words https://target-venue.example

# common suffixes
psudohash --words /tmp/site.words --years 2020-2026 \
  --append-numbering 2 --output /tmp/site-boosted.txt

hashcat -m 22000 hs.22000 /tmp/site-boosted.txt -r best64.rule
```

## Session save / resume

```
hashcat --session=defcon -m 22000 hs.22000 rockyou.txt -r OneRule.rule
# Ctrl-C to pause (writes session file).
hashcat --session=defcon --restore
```

## GPU tuning

- `-w 4` — insane workload (max card utilization).
- `-O` — optimized kernel; caps password length but is faster.
  For `-m 22000 -O` the optimized-kernel cap is **32 characters**
  (not 63). The WPA/WPA2 passphrase spec allows up to 63 ASCII
  chars — so `-O` will silently miss any candidate longer than 32.
  Drop `-O` if the target password space might exceed 32 chars.
- `--status --status-timer=5` — periodic ETA output.
- `--gpu-temp-abort=90` — safety cap on toaster laptops.
- `--keep-guessing` — keep running past first crack (some captures
  contain multiple 4-ways for the same ESSID with different PSKs,
  e.g., temp guest network next to primary).
- `--potfile-disable` — skip auto-remembering (useful for
  reproducible benchmarks).
- `--potfile-path=/path/to/pot` — custom potfile; combine with
  `--session=<name>` for per-target restore.
- `--restore` — resume the last session from the CWD. **Caveat:**
  hashcat's restore file is CWD-relative; run `--restore` from the
  directory you started the session in, or pass `--session=<name>`
  explicitly.

## GPU baselines (2024 reference, mode 22000)

| GPU           | H/s (no `-O`) | H/s (`-O`)   | notes                    |
| ---           | ---           | ---          | ---                      |
| RTX 3080      | ~750 KH/s     | ~900 KH/s    | 320 W baseline           |
| RTX 3090      | ~1.1 MH/s     | ~1.4 MH/s    | 350 W baseline           |
| RTX 4080      | ~1.5 MH/s     | ~1.8 MH/s    |                          |
| RTX 4090      | ~2.0 MH/s     | ~2.4-2.6 MH/s| 450 W; the standard 2024 |
| M2 Max        | ~200 KH/s     | ~250 KH/s    | Apple Neural Engine      |

## Post-crack validation

Once hashcat spits out a PSK candidate, verify it decrypts real
traffic before claiming the flag:

```
# 1. Trial-associate with wpa_supplicant
cat > /tmp/verify.conf <<EOF
network={
    ssid="<ESSID>"
    psk="<candidate PSK>"
    key_mgmt=WPA-PSK
}
EOF
sudo wpa_supplicant -i wlan1 -c /tmp/verify.conf -B
sudo dhclient wlan1

# 2. Or, offline: decrypt a data frame in Wireshark
tshark -r cap.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"wpa-pwd\",\"<PSK>:<ESSID>\"" \
  -Y "data and not eapol" -c 5
# If the plaintext DA/SA and IP fields look right, PSK is confirmed.
```

## Candidate generation for vendor defaults

`hcxpsktool` generates candidate PSKs for known vendor default
schemes (Comcast xfinity, Netgear, Belkin, D-Link, TP-Link,
Verizon Fios). Feed its output into hashcat:

```
hcxpsktool -a AA:BB:CC:DD:EE:FF > /tmp/candidates.txt
hashcat -m 22000 hs.22000 /tmp/candidates.txt
```

## Distributed cracking

- **hashtopolis** — Django/Postgres/redis coordinator. Split
  wordlists / masks across N workers.
- **hashcat brain** — real-time candidate deduplication across
  workers.

## Comparing to `airodump-ng+aircrack-ng`

`aircrack-ng` still works but is CPU-only, single-format, and
uses PMK cache poorly. hashcat with mode 22000 is the current
standard.

## Failure modes

- **`--force` says the OpenCL platform is missing.** Install the
  vendor's OpenCL runtime (nvidia-opencl, ROCm, or Apple's built-in).
- **Very slow (< 10 KH/s).** You're on the CPU. Confirm with `-I`
  that hashcat sees your GPU.
- **Cracks to a wrong candidate.** hashcat's WPA2 crack has a
  vanishingly small false-positive rate but check with
  `wpa_supplicant`'s trial association or Wireshark decrypt.
- **`WPA*01` line but PMKID mismatch.** hcxpcapngtool sometimes
  emits from a leaked M1 that isn't for the right ESSID. Filter
  the pcap with `hcxpcapngtool --essid=<name>` first.

## Cite

- hashcat.net wiki — example hashes and rule catalog.
- Steube 2018 — mode 22000 introduction.
- hcxtools GitHub — hcxpcapngtool format.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`,
  `hashcat-5500-mschapv2-crack`.
