# cracking-tradecraft — reference

## Attack modes (hashcat `-a`)

| -a | name       | shape                                     |
| -- | ---------- | ----------------------------------------- |
| 0  | Straight   | wordlist ± rules (`-r`)                   |
| 1  | Combinator | left wordlist × right wordlist            |
| 3  | Mask       | position-per-position character sets      |
| 6  | Hybrid W+M | wordlist prefix, mask suffix              |
| 7  | Hybrid M+W | mask prefix, wordlist suffix              |
| 9  | Association| known keyspace vs. a specific hash (rare) |

WPA PSK is 8..63 printable ASCII. Everything below assumes that
range (hashcat's optimized kernel for mode 22000 respects it).

## Mask character classes

| token | class          | example                |
| ----- | -------------- | ---------------------- |
| `?l`  | lowercase      | `a..z`                 |
| `?u`  | uppercase      | `A..Z`                 |
| `?d`  | digit          | `0..9`                 |
| `?s`  | symbol         | ``!"#$%&'()*+,-./…``   |
| `?a`  | any printable  | `?l?u?d?s`             |
| `?b`  | any byte       | `\x00..\xff`           |
| `?1..?4` | user-defined | `-1 ?l?d` then `?1?1?1` |

Common WPA PSK patterns to try in order:

- `?d?d?d?d?d?d?d?d` — 8 digits (WPS-derived defaults)
- `?l?l?l?l?l?l?l?l` — 8 lowercase
- `?l?l?l?l?d?d?d?d` — word + 4 digits (Kevin1985)
- `?u?l?l?l?l?l?d?d` — capitalized + 2 digits (Cookie12)
- `?l?l?l?l?l?l?d?d?d?d` — 6-letter + 4-digit (autumn2024)
- `-1 ?l?d ?1?1?1?1?1?1?1?1?1?1` — 10 lower+digit mix

## Rule catalog (the ones worth stacking)

| rule                       | size | notes                          |
| -------------------------- | ---- | ------------------------------ |
| `best64.rule`              | 64   | first pass, always             |
| `T0XlC.rule`               | ~4k  | historical dive; mostly bespoke|
| `d3ad0ne.rule`             | ~34k | medium depth; hours on rockyou |
| `dive.rule`                | ~99k | heavy; day+ on rockyou         |
| `OneRuleToRuleThemAll.rule`| ~52k | community-standard heavy pass  |

Rules run left-to-right on each wordlist entry. Stack sparingly —
`rockyou × dive × best64` explodes the keyspace by 6M×.

## PMKID vs. 4-way cost

Same PMK derivation (PBKDF2-HMAC-SHA1 4096 iterations of the
passphrase with ESSID as salt). Per-guess GPU cost is *identical*.
The difference is capture-side ergonomics, not crack-side speed.

- **hashrate on a single RTX 4090** (2024 reference): ~2.4 MH/s
  for mode 22000.
- **rockyou.txt straight** ≈ 6 seconds for 14M candidates.
- **rockyou × OneRule** ≈ 100 minutes.
- **`?a?a?a?a?a?a?a?a` full 8-char printable brute** ≈ 33 days at
  2.4 MH/s. Move to masks / SSID-derived wordlists instead.

## Wordlist ingredients

| source            | typical yield             |
| ----------------- | ------------------------- |
| `rockyou.txt`     | 14M common leaked passes  |
| `crackstation-human-only` | 63M leaked            |
| `weakpass_3a`     | 1B+ (space consideration) |
| SSID-derived (`cewl`) | 100–2000 (venue-specific) |
| con-attendee first-name lists | ~5k (regional) |
| `psudohash` outputs | rockyou scale ×3–10     |

## Session ergonomics

- `--session=<name>` — name the run.
- Ctrl-C writes session state.
- `--restore` — resume the named session.
- `--status --status-timer=5` — periodic ETA.

## GPU tuning

- `-w N` — workload profile: 1 (low, foreground) .. 4 (insane).
- `-O` — optimized kernel; requires passphrase ≤ 63 (safe for WPA).
- `--gpu-temp-abort=90` — safety cap.
- `-d N` — bind to a specific device (multi-GPU).
- `-D 1,2` — CPU + GPU device types together (usually just `-D 2`).

## Distributed

- **`hashtopolis`** — Django/Postgres coordinator; agents on the
  laptops of your teammates.
- **`hashcat --brain-client`** — real-time cross-agent dedup.
- Split masks with `--skip` / `--limit`, wordlists by row range,
  rules by file. `-s` = skip N; `-l` = limit N.

## Cite

- hashcat.net wiki — rule spec, mask spec, brain docs.
- Steube 2018 — mode 22000.
- hcxtools GitHub — capture format that feeds mode 22000.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`.
