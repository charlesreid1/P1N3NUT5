# cracking-tradecraft — walkthrough

Reach for these in order, cheapest first. Every `hs.22000` file feeds
the same pipeline; the only variable is *how* you generate candidates.

## Path 0 — rockyou baseline (30 seconds)

Always start here, even when you "know" it won't hit. Instant on any
GPU; occasionally works on ISP-issued gear that was factory-reset.

```
hashcat -m 22000 hs.22000 rockyou.txt -w 4 --status
```

## Path 1 — rockyou + best64 (< 5 minutes)

```
hashcat -m 22000 hs.22000 rockyou.txt -r best64.rule -w 4
```

`best64` covers case flips, digit appends, l33t swaps — the modal
"tweak my remembered password" transformations.

## Path 2 — rockyou + OneRuleToRuleThemAll (1–2 hours)

```
hashcat -m 22000 hs.22000 rockyou.txt -r OneRuleToRuleThemAll.rule
```

Depth pass on rockyou. Cover 95% of the empirical human-password
distribution. Anything past this needs domain knowledge.

## Path 3 — masks tailored to structure

If Path 2 dies, guess the structure. Common WPA PSK shapes and
runtimes at ~2 MH/s:

```
# 8 digits — WPS-defaulted APs; instant.
hashcat -m 22000 hs.22000 -a 3 ?d?d?d?d?d?d?d?d

# 10 digits — some phone-number-length ISP defaults; 5 seconds.
hashcat -m 22000 hs.22000 -a 3 ?d?d?d?d?d?d?d?d?d?d

# Word + 4 digits (Kevin1985 pattern); minutes.
hashcat -m 22000 hs.22000 -a 3 ?l?l?l?l?l?l?d?d?d?d

# Cap + 5 lower + 2 digits (Autumn24 pattern); minutes.
hashcat -m 22000 hs.22000 -a 3 ?u?l?l?l?l?l?d?d
```

`?a?a?a?a?a?a?a?a` (all printable, 8 chars) is **~87 years** at
2.4 MH/s — 95^8 ≈ 6.634e15 candidates ÷ (2.4e6 H/s × 86400 s/day)
≈ 31 990 days. Don't. Structure-first.

## Path 4 — SSID-derived wordlist

```
# 1. Scrape venue's website for words + phrases.
cewl -d 3 -m 4 -w /tmp/venue.words https://venue.example
wc -l /tmp/venue.words

# 2. Boost with year suffixes + common transforms.
psudohash --words /tmp/venue.words \
  --years 2020-2026 \
  --append-numbering 2 \
  --output /tmp/venue-boosted.txt

# 3. Crack.
hashcat -m 22000 hs.22000 /tmp/venue-boosted.txt \
  -r best64.rule -w 4
```

Con-attendee first-name lists (Reddit /r/whatsapp public dumps or
similar) give another ~5k candidates. Same recipe.

## Path 5 — Hybrid (word + mask)

Someone's password is definitely `flag2024` or `p1n3nuts!!` and
straight rockyou missed the mask suffix. Bolt one on:

```
# rockyou word, then 4 digits
hashcat -m 22000 hs.22000 -a 6 rockyou.txt ?d?d?d?d

# rockyou word, then 1 symbol + 4 digits
hashcat -m 22000 hs.22000 -a 6 rockyou.txt ?s?d?d?d?d
```

## Path 6 — Session + resume

Long runs need pausing:

```
hashcat --session=defcon -m 22000 hs.22000 rockyou.txt \
  -r OneRuleToRuleThemAll.rule

# Ctrl-C to stop cleanly (writes .restore file).
hashcat --session=defcon --restore
```

## Path 7 — Multi-GPU / distributed

- **Multi-GPU on one host**: hashcat auto-detects. `-d 1,2,3` to
  pin subsets. `-w 4` uses all cores of all cards.
- **hashtopolis**: split rockyou across N agents by row range with
  `--skip` / `--limit`.
- **`--brain-client`**: real-time cross-agent dedup so agents don't
  duplicate work.

## Path 8 — Vendor default derivation

If the SSID matches a known-vendor regex, skip cracking and derive
directly. See `default-psk-derivation/walkthrough.md`.

## What if nothing works?

- **Verify the capture.** Bad `hs.22000` lines waste days. Re-run
  `hcxpcapngtool --info <pcap>` and check the frames it parsed.
  A malformed EAPOL or wrong ESSID hex kills the crack silently.
- **PSK is > 12 chars random.** Cracking is not the path; look for
  other attack surface (PMKID leak on a related AP, WPS on a
  neighbor, transition-mode side).
- **The puzzle isn't WPA-PSK.** Confirm the AKM in the RSN IE.

## Cite

- hashcat.net wiki — rule / mask spec.
- Steube 2018 — mode 22000.
- `psudohash` GitHub, `cewl` docs.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`.
