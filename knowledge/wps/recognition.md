# WPS — recognition

The WPS IE tells you almost everything before you spend a Reaver
attempt. Read it first.

## The WPS IE (Element ID 221, OUI 00-50-F2, subtype 4)

Fields to read from beacons and probe responses:

| field                | meaning                                          |
| -------------------- | ------------------------------------------------ |
| Version              | 1.0 or 2.0                                       |
| WPS State            | 1 = not configured, 2 = configured               |
| AP Setup Locked      | 0 = unlocked, 1 = locked out                     |
| Selected Registrar   | is a registrar currently active?                 |
| Device Password ID   | PIN, PBC, machine-specified, etc.                |
| Response Type        |                                                  |
| UUID-E               | AP's UUID (identical across reboots)             |
| Manufacturer         | vendor string (often the tell)                   |
| Model Name           | product line                                     |
| Model Number         | firmware generation                              |
| Serial Number        | serial (rarely useful)                           |
| Primary Device Type  | AP / bridge / router                             |
| Device Name          | user-configurable                                |

Wireshark filter:

```
wlan.tag.number == 221 && wlan.tag.oui == 0x0050f2 &&
wlan.wfa.ie.wpa.subtype != 1
```

## Is WPS actually usable?

- **WPS State = 2 (Configured), Locked = 0** → active target. Try
  Pixie Dust and Reaver.
- **Configured, Locked = 1** → locked out. Wait for the reset
  window (typically 60 s, vendor-dependent) or try
  `wps-locked-bypass-timing`.
- **Not Configured (state = 1)** → no PIN set yet. Rare in the
  wild; Reaver flows still work but no PSK to recover.
- **WPS IE absent entirely** → no WPS. Move on.

## Vendor Pixie Dust likelihood

Pixie Dust works when the AP uses predictable random-number
generation for the E-S1 / E-S2 nonces. Historically vulnerable:

- **Broadcom** — many generations. Pixie Dust often instant.
- **Ralink / MediaTek** — historically weak PRNG.
- **Realtek** — some generations vulnerable.
- **Atheros** — mixed; many generations patched.
- **AirTies, Belkin, D-Link, Linksys pre-2015** — generally
  Pixie-eligible depending on chipset.

## Vendor PIN algorithms

Some vendors ship default PINs derived from the MAC:

- **Belkin** — MAC-based, generation-specific.
- **D-Link (some)** — MAC-based via `dlink-pin.py` or equivalent.
- **TP-Link (some gen)** — MAC-based.
- **Netgear (some gen)** — MAC-based.

See `default-psk-derivation/reference.md` for algorithm sources.

## Null-PIN and negative-PIN candidates

- **Null PIN** (empty string) — some ISP-supplied gear accepts.
  Try first as a 30-second test.
- **Negative PIN** — some chipsets accept PIN = "12345670" (or
  variants) as a debug backdoor. Vendor-specific.

## What the WPS Manufacturer leak gives you

Even when WPS is "disabled," some APs still emit the WPS IE with
Manufacturer / Model populated. That leak is often enough to:

- Identify the chipset → predict Pixie Dust likelihood.
- Match a vendor-default-PSK regex → derive PSK without touching WPS.
- Fingerprint firmware generation → correlate with CVE tables.

## What a WIDS sees

Reaver flow generates hundreds of WPS M1/M2 exchanges. Extremely
loud. Modern enterprise WIDS flags "WPS brute-force" within seconds.
Not stealthy — but reliable when it works.

## When to skip WPS

- **Locked out** with a long reset window (some vendors 1 hour+).
- **AP not vulnerable to Pixie Dust** and PIN pool wasn't reduced
  by vendor derivation → 11k trials at ~1 PIN/sec = 3 hours worst
  case.
- **You have a captured PMKID + rockyou** — likely faster path.

## Cite

- Wi-Fi Alliance — WPS Specification 2.0.
- CVE-2011-5053 — original WPS PIN vulnerability.
- Viehböck 2011 — Reaver public disclosure.
- Bongard 2014 — Pixie Dust.
- attacks.json: `wps-reaver-online`, `wps-pixie-dust`,
  `wps-null-pin`, `wps-negative-pin`,
  `wps-vendor-pin-derivation`, `wps-locked-bypass-timing`,
  `wps-pbc-window-abuse`, `wps-hcxlabtool-aggressive`.
