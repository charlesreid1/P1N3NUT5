# hardware-and-antennas — reference

Antennas, dBi, TX caps, adapter chipset table. Tuning matters at a
con — the difference between "capture in 5 minutes" and "capture in
5 hours" is often antenna choice plus positioning.

## Antenna types

| type       | gain (typ)   | pattern                     | when to reach for      |
| ---------- | ------------ | --------------------------- | ---------------------- |
| Dipole     | 2–5 dBi      | Omnidirectional (donut)     | General survey         |
| Panel      | 8–14 dBi     | Broad forward sector, ~60°  | Isolate a target from ambient scrum |
| Yagi       | 12–18 dBi    | Narrow forward beam, ~30°   | Long-range single target |
| Biquad     | 10–12 dBi    | Broad forward sector        | DIY / low-cost panel   |
| Parabolic  | 18–24 dBi    | Very narrow, <15°           | Extreme range, static  |
| Rubber-duck| 1–2 dBi      | Slightly omnidirectional    | Stock adapter          |

**Gain is not amplification.** A high-gain antenna trades off some
directions for others. A 24 dBi parabolic is deaf to anything off-
axis. At a con floor with APs everywhere, a panel (~9 dBi, 60°) is
the best-cost tradeoff.

## dBi vs dBd

- **dBi** — gain over an isotropic radiator (theoretical omnidir
  point source). Most vendors quote this.
- **dBd** — gain over a half-wave dipole. dBi = dBd + 2.15.

Add or subtract 2.15 to convert. Vendor claims are usually dBi.

## Band coverage

Antennas are frequency-band-tuned:

- **2.4 GHz-only** — cheapest, most common. Won't work on 5 or 6 GHz.
- **5 GHz-only** — enterprise-focused.
- **Dual-band 2.4/5 GHz** — most consumer.
- **Tri-band 2.4/5/6 GHz** — Wi-Fi 6E era. Read the datasheet — many
  "tri-band" claims actually cover only 2.4 + 5 with 6 GHz being
  best-effort.

## TX power caps

Two different numbers get conflated. Keep them separate:

- **Conducted TX power** — what the radio pushes into the antenna
  port, measured in dBm. This is what `iw dev wlan0 set txpower` and
  `iwconfig ... txpower` control.
- **EIRP (Equivalent Isotropic Radiated Power)** — conducted TX
  power + antenna gain (in dBi) − cable loss. This is what the
  regulator actually caps.

Regulatory caps by band / region (point-to-multipoint unless noted):

| Band            | Region | Conducted TX (dBm) | Antenna gain (dBi) | EIRP (dBm) | Notes |
| --------------- | ------ | ------------------ | ------------------ | ---------- | ----- |
| 2.4 GHz         | US     | ≤ 30               | ≤ 6                | ≤ 36       | Point-to-point may exceed 36 dBm EIRP via the 3-for-1 rule: each 3 dBi of gain above 6 dBi permits 1 dB conducted reduction, so EIRP rises while conducted TX falls. |
| 5 GHz UNII-1    | US     | ≤ 30               | ≤ 6                | ≤ 36       | Indoor + outdoor since 2014 rules update. |
| 5 GHz UNII-2A/C | US     | ≤ 24               | ≤ 6                | ≤ 30       | DFS required. |
| 5 GHz UNII-3    | US     | ≤ 30               | ≤ 6                | ≤ 36       | Point-to-point ≤ 53 dBm EIRP (fixed link rules). |
| 6 GHz LPI       | US     | ≤ 24               | —                  | ≤ 30       | Wi-Fi 6E indoor, no AFC. |
| 6 GHz SP        | US     | ≤ 30               | —                  | ≤ 36       | Standard Power; requires AFC coordination. |
| 6 GHz VLP       | US     | —                  | —                  | ≤ 14       | Very Low Power portable. |
| 2.4 GHz         | EU     | —                  | —                  | ≤ 20       | ETSI EN 300 328. |
| 5 GHz UNII-1    | EU     | —                  | —                  | ≤ 23       | Indoor. |
| 5 GHz UNII-2    | EU     | —                  | —                  | ≤ 30       | DFS + TPC required. |
| 2.4 / 5 GHz     | JP     | —                  | —                  | varies     | Some UNII-2 sub-band restrictions; consult MIC. |

Above these caps, cards drop TX silently or the driver refuses.
`iw reg get` and `iw phy phy0 info` show what your driver honors.

## Adapter chipset table (2026)

| adapter                | chipset                   | monitor  | injection | 5 GHz | 6 GHz | notes                              |
| ---------------------- | ------------------------- | -------- | --------- | ----- | ----- | ---------------------------------- |
| Alfa AWUS036ACH        | RTL8812AU                 | yes      | yes       | yes   | no    | Classic dual-band; driver quirks   |
| Alfa AWUS036ACM        | MT7612U                   | yes      | yes       | yes   | no    | Modern, mt76 upstream              |
| Alfa AWUS036AXML       | MT7921AU                  | yes      | partial   | yes   | limited | Wi-Fi 6; 6 GHz driver support varies |
| Alfa AWUS036NHA        | AR9271                    | yes      | yes       | no    | no    | ath9k gold standard, 2.4 GHz only  |
| Panda Wireless PAU09   | RT5372                    | yes      | yes       | no    | no    | Cheap 2.4 GHz workhorse            |
| TP-Link Archer T2U     | RTL8811AU                 | limited  | limited   | yes   | no    | Kernel-version-dependent           |
| TP-Link Archer T3U     | RTL8812BU                 | limited  | limited   | yes   | no    | Driver in tree since Linux 5.10+   |
| Netgear A6210          | MT7612U                   | yes      | yes       | yes   | no    | Same silicon as AWUS036ACM         |
| Intel AX210 (M.2)      | iwlwifi                   | limited  | no        | yes   | yes   | Great client, poor attacker card   |
| Intel AX411 (M.2)      | iwlwifi                   | limited  | no        | yes   | yes   | Same story                         |
| Pineapple Mk VII wlan1 | MT7615 (mt76)             | yes      | yes       | yes   | no    | Built-in dual-band radio; authoritative spec: `pineapple-mk7/reference.md` |
| Pineapple Mk VII wlan0 | MT7628AN (mt76)           | yes      | yes       | no    | no    | Built-in 2.4 GHz radio on the Mark VII SoC |

## Rehoming the Pineapple's antennas

Stock Pineapple ships with 5 dBi dipoles. Upgrades:

- **Con floor, dense** → 9 dBi dipoles or a small 8 dBi panel.
- **Bench engagement** → 12 dBi panel aimed at the target.
- **Single-target extreme range** → 15 dBi yagi.

Antenna connectors on Mk VII are RP-SMA (reverse-polarity). Match
the connector or use an adapter — a plain SMA won't seat.

## Cite

- FCC Part 15 subpart E — US 5 / 6 GHz EIRP rules.
- ETSI EN 300 328 / EN 301 893 — EU 2.4 / 5 GHz rules.
- Alfa Network, Panda Wireless, TP-Link vendor datasheets.
- kernel.org linux-wireless driver matrix.
- Hak5 — Mark VII hardware specification.
