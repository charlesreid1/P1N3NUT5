# WPA3 recognition

## AKM suite selectors in the RSN IE

- **`00-0F-AC:08`** — SAE (Dragonfly hunt-and-peck; original).
- **`00-0F-AC:18` = 24 decimal** — SAE-EXT-KEY (H2E — Dragonblood
  mitigation).
- **`00-0F-AC:0C` = 12 decimal** — OWE (Opportunistic Wireless
  Encryption). Not a passphrase mode; treat separately.
- **`00-0F-AC:02` = 2** alongside AKM 8 — transition mode. Fast lane.

## Transition vs. WPA3-only

- **RSN IE lists 8 (or 24) alone** → WPA3-only.
- **RSN IE lists 2 and 8 both** → transition mode. Attack the WPA2
  side.

## PMF status

WPA3 mandates PMF-required. In the RSN Capabilities field:

- **MFPR bit (bit 7) = 1** — Management Frame Protection Required.
- **MFPC bit (bit 6) = 1** — MFP Capable.

Both should be set on a spec-compliant WPA3 beacon. If MFPR=0 on a
"WPA3-only" AP, that's a misconfiguration.

## SAE Group support

- SAE Commit frames carry a Finite Cyclic Group Field (2 bytes).
- Common: **19** (P-256, default), **20** (P-384), **21** (P-521).
- Legacy MODP: **22, 23, 24** — presence means the hunt-loop timing
  oracle is live (Dragonblood-timing applies).

## H2E on the wire

- **AKM 24 (SAE-EXT-KEY)** — H2E capable. Constant-time PWE.
- **AKM 8 without AKM 24** — hunt-and-peck PWE. Vulnerable to the
  original Dragonblood side channels.
- **Both present** — mixed; the client picks. Weak clients pick 8.

## 6 GHz — WPA3-only

6 GHz operating class 131–137 forbids WPA2. Any 6 GHz AP is WPA3-only
by regulation. Transition-mode downgrade is off the table on 6 GHz;
attack the 2.4/5 GHz side if the network is dual-band.

## Cite

- IEEE Std 802.11-2020, §9.4.2.24, §12.4.
- Wi-Fi Alliance WPA3 Specification.
