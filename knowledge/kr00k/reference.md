# Kr00k — all-zero PTK on disassoc

Broadcom / Cypress WiFi chipsets (and later a Qualcomm Atheros variant)
have a bug in their firmware disassociation handler: when a STA sees
a disassoc, any frames still in the encryption queue are transmitted
using an **all-zero pairwise transient key** rather than being dropped.
An attacker who can capture the tail-frame handful on the air can then
decrypt them offline with a known zero key.

## Trigger + affected chipsets

- **CVE-2019-15126** — Broadcom BCM4339/4358/4356, Cypress inheritors.
  Trigger: attacker sends a spoofed disassoc frame; victim's chipset
  flushes its pending encryption queue with PTK=0.
- **CVE-2020-3702** — Qualcomm Atheros variant. IPQ8064, QCA9377,
  Snapdragon-family Wi-Fi front-ends. Same primitive, longer patch tail.

## Affected devices in 2026

Flagship phones are patched. The tail lives on:

- Older Amazon Echo / Kindle
- WiFi cameras (Wyze, Amcrest, cheap OEM)
- Older iPhone / iPad revs on end-of-life iOS
- Older Raspberry Pi WiFi HATs on Cypress chips
- Many IoT hubs / smart-home bridges

## Cite

- ESET 2020 — Kr00k white paper + detector release.
- CVE-2019-15126, CVE-2020-3702.
- attacks.json: `kr00k-broadcom-cve-2019-15126`, `kr00k-qca-cve-2020-3702`.
