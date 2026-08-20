# WPA3 recognition

## AKM suite selectors in the RSN IE

Per IEEE 802.11-2020 Table 9-151. Wire byte hex → decimal AKM number:

- **`00-0F-AC:08` = AKM 8** — SAE (original Dragonfly). Uses
  hunt-and-peck PWE **unless** the RSNXE H2E bit is also set.
- **`00-0F-AC:18` = AKM 24** — SAE-EXT-KEY. Extended-key SAE with
  HMAC-SHA-384 KDF, paired with GCMP-256. Implies H2E.
- **`00-0F-AC:12` = AKM 18** — OWE (Opportunistic Wireless
  Encryption). Not a passphrase mode; treat separately.
- **`00-0F-AC:0C` = AKM 12** — 802.1X Suite-B-192 (WPA3-Enterprise
  192-bit). NOT OWE.
- **`00-0F-AC:02` = AKM 2** alongside AKM 8 — WPA3 transition mode.
  Fast lane; attack the WPA2 side.

**Common mistake.** The hex byte in the wire selector is the same
decimal as the AKM number (0x18 = 24, 0x12 = 18, 0x0C = 12). AKM 18
= OWE ≠ AKM 24 = SAE-EXT-KEY. See [[akm-selector-glossary]].

## Transition vs. WPA3-only

- **RSN IE lists 8 (or 24) alone** → WPA3-only.
- **RSN IE lists 2 and 8 both** → transition mode. Attack the WPA2
  side.

## PMF status

WPA3 mandates PMF-required. In the RSN Capabilities field:

- **MFPR bit (bit 6) = 1** — Management Frame Protection Required.
- **MFPC bit (bit 7) = 1** — MFP Capable.

Both should be set on a spec-compliant WPA3 beacon. If MFPR=0 on a
"WPA3-only" AP, that's a misconfiguration.

## SAE Group support

- SAE Commit frames carry a Finite Cyclic Group Field (2 bytes).
- Common: **19** (P-256, default), **20** (P-384), **21** (P-521).
- Legacy MODP: **22, 23, 24** — presence means the hunt-loop timing
  oracle is live (Dragonblood-timing applies).

## H2E on the wire — RSNXE, not AKM

H2E (Hash-to-Element / SAE-PT) is signaled by the **RSN Extension
Element (RSNXE, IE 244)** — specifically bit 5 of the RSNX
Capabilities field ("SAE H2E only"). It is NOT a separate AKM
number.

- **AKM 8 + RSNXE H2E bit set** — SAE with constant-time PWE.
- **AKM 8, RSNXE absent or bit clear** — hunt-and-peck PWE.
  Vulnerable to the original Dragonblood side channels.
- **AKM 24 (SAE-EXT-KEY)** — extended-key SAE for GCMP-256; implies
  H2E.
- **AKM 8 and AKM 24 both present** — mixed; the client picks. Weak
  clients pick 8 with hunt-and-peck.

## 6 GHz — WPA3-only

6 GHz operating class 131–137 forbids WPA2. Any 6 GHz AP is WPA3-only
by regulation. Transition-mode downgrade is off the table on 6 GHz;
attack the 2.4/5 GHz side if the network is dual-band.

## Cite

- IEEE Std 802.11-2020, §9.4.2.24, §12.4.
- Wi-Fi Alliance WPA3 Specification.
