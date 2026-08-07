# default-psk-derivation — reference

## The derivation catalog

Every entry maps to `default_psks.json` and to a `default-psk-*`
record in `attacks.json`. Each has an SSID regex you can match against
beacons and a derivation algorithm.

| record id                 | vendor / gen                     | region  | SSID regex                     | still 2026? |
| ------------------------- | -------------------------------- | ------- | ------------------------------ | ----------- |
| `dpsk-upc-ubee`           | UPC / UBEE (Liberty Global)      | EU      | `^UPC\d{7}$`                   | yes         |
| `dpsk-thomson-speedtouch` | Thomson SpeedTouch               | mostly EU | `^SpeedTouch[A-F0-9]{6}$`     | rare        |
| `dpsk-bt-home-hub`        | BT Home Hub 2 / 3 / 4            | UK      | `^BTHub\d-\w{4}$`              | some        |
| `dpsk-sky-broadband`      | Sky Broadband (SR-family)        | UK      | `^SKY\w{5}$`                   | yes         |
| `dpsk-livebox-sagemcom`   | Orange Livebox (Sagemcom)        | FR      | `^Livebox-\w{4}$`              | yes         |
| `dpsk-netgear-genie`      | Netgear Genie default            | US/UK   | `^NETGEAR\d\d$`                | some (pre-2020) |
| `dpsk-technicolor`        | Technicolor consumer             | wide    | `^Technicolor.{4}$`            | yes         |
| `dpsk-airties`            | AirTies                          | TR / EU | `^AirTies_Air\d{4}_[A-F0-9]{4}$` | yes       |
| `dpsk-vodafone-easybox`   | Vodafone EasyBox                 | DE      | `^EasyBox-\w{6}$`              | some        |
| `dpsk-alice`              | Alice-Gate / Alice-Box (Telecom Italia) | IT | `^Alice-\d{8}$`             | rare        |
| `dpsk-orange-livebox-old` | Orange Livebox (older gens)      | FR      | `^Livebox-\w{4}$`              | rare        |
| `dpsk-huawei-hg8xxx`      | Huawei HG8xxx GPON ONT           | wide    | `^HG8\d{3}-\w{4}$`             | yes         |
| `dpsk-zte-h298`           | ZTE H298x                        | wide    | `^ZTE-H298\w{4}$`              | yes         |
| `dpsk-comcast-xfinity-legacy` | Comcast Xfinity                | US      | (variable — see record)        | rare        |
| `dpsk-belkin`             | Belkin (also WPS PIN algorithm)  | wide    | `^belkin\.\w{3}$` / `^Belkin_\w{6}$` | some  |

## How each derivation works

Each vendor's algorithm reads a small piece of public data from the
beacon and produces a small candidate list.

- **UPC/UBEE** — `upc_keys` binary. Input: SSID suffix (7 digits).
  Output: ~8 candidate PSKs (8 uppercase alphanumeric each). Verify
  by trial-decrypt or PMKID match.
- **Thomson SpeedTouch** — SSID contains 6 hex chars of the serial;
  the PSK is a 10-hex-char hash of the full serial. `stkeys` /
  `SpeedTouch keygen`. Enumerate the 3 missing serial chars → ~4096
  candidates.
- **BT Home Hub** — PSK derived from the last 4 chars of the SSID
  (which encode a serial fragment). Small candidate list; `bthub-tools`.
- **Sky Broadband SR** — PSK derived from BSSID via a fixed
  transformation; single candidate. `sky-router-keygen`.
- **Livebox / Sagemcom** — SSID suffix encodes 4 chars of the serial.
  Full derivation via `LivePwn` / `livebox-pwn`. Multi-candidate.
- **Netgear Genie (pre-2020)** — PSK is a Wi-Fi Alliance-formatted
  passphrase from a fixed wordlist ×2 words + digits.
  Wordlist-enumeration cracker.
- **Technicolor** — SSID has 4 chars matching BSSID last 4 bytes; PSK
  derived from BSSID. `TechnicolorGateway keygen`.
- **AirTies** — SSID `AirTies_Air<model>_<hex4>`. PSK from serial.
- **Vodafone EasyBox** — SSID has last 6 chars of MAC; PSK from MAC.
- **Alice** — SSID has 8-digit serial suffix; PSK derived from serial.
- **Huawei HG8xxx** — SSID has last 4 of MAC; PSK from serial (varies
  by regional firmware).
- **ZTE H298x** — SSID has 4 hex of MAC; PSK from MAC.
- **Belkin** — WPS PIN algorithm; PSK not deterministic but WPS is
  the pivot.
- **Xfinity legacy** — vendor doc-based PSK on early generations.

## Beacon-observable inputs

The beacon carries everything the derivation needs, without
associating:

- **SSID string** — matches the regex above; often contains the
  serial fragment directly.
- **BSSID (Address 3 in the beacon)** — the AP's MAC; some
  derivations use it directly.
- **WPS IE Manufacturer / Model** — often confirms the vendor and
  firmware generation.
- **Vendor-Specific IE OUIs** — cross-reference against a vendor
  table.

## Verifying a candidate

Two options:

1. **PMKID match.** Capture a PMKID (see `pmkid/walkthrough.md`) and
   trial-crack against the candidate list. hashcat mode 22000 accepts
   the candidate list as a wordlist.
2. **4-way trial decrypt.** If a handshake is already captured,
   trial-decrypt a data frame with each candidate (see
   `post-crack-rf/walkthrough.md`).

## Cite

- `upc-keys` GitHub — canonical UPC derivation source.
- Bongard / stkeys — Thomson SpeedTouch keygen.
- Publicly-released vendor derivation code (referenced in each
  `default_psks.json` record).
- IEEE Std 802.11-2020 §9.4.2.24 (RSN IE), §9.4.2.11 (Vendor-Specific).
- attacks.json: every `default-psk-*` record.
