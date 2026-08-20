# Kr00k recognition

Which devices are still Kr00k-vulnerable in 2026, and how you identify
them from the air.

## Chipset fingerprint

Kr00k is a chipset bug, not an OS bug. Two CVE families:

- **CVE-2019-15126 (Broadcom / Cypress).** Original ESET disclosure,
  2019. Affected: BCM4339, BCM4345, BCM4358, BCM4356, BCM43602,
  Cypress CYW43xx family (Cypress inherited Broadcom's WiFi division).
- **CVE-2020-3702 (Qualcomm Atheros).** 2020 follow-up. Affects
  QCA6174, QCA9377, IPQ4019, and a range of derivatives found in
  older Amazon Echo, some smart TVs, and IoT gateways.

Identify a client's chipset:

- **OUI of the client MAC** — the first 3 bytes map to the vendor of
  the network chip when the vendor doesn't randomize. Broadcom's
  OUIs (14:23:F2, 5C:0A:5B, D0:03:4B, and dozens more) reveal a
  Broadcom radio; QCA prefixes (14:B4:57, 24:0A:64, 90:F6:52, …)
  reveal a QCA radio.
- **Probe request IE order and support bits** — see
  `fingerprinting/reference.md`. Broadcom/Cypress and QCA firmwares
  each leave distinct IE-order signatures.
- **Vendor-specific IEs in association request.** Broadcom's WPS IE
  and Extended Capabilities layout differs from QCA's.

MAC randomization defeats OUI-based ID; probe-IE fingerprinting still
works.

## Devices still likely vulnerable in 2026

- **Older iPhone / iPad (pre-A11 Bionic era)** — Broadcom BCM4339 /
  BCM4345. iOS updates patched the disassoc trigger on many models
  but iOS 12–13 devices left on those releases remain vulnerable.
- **Amazon Echo (1st, 2nd gen; some Show variants).** BCM4358 or QCA
  in different SKUs; long tail of unpatched firmware.
- **Kindle (older Paperwhite, Voyage).** Broadcom, patched partially.
- **Older Roku, Chromecast.** Some SKUs on Cypress/Broadcom, patched
  status per-SKU.
- **WiFi cameras / doorbells (Wyze early gen, Ring 1st gen).**
  Cypress-family; firmware update cadence poor.
- **Smart TVs (Samsung / LG 2017–2019 lines).** Broadcom common.
- **Embedded IoT gateways / hubs** — QCA IPQ family; the CVE-2020-3702
  tail is long here.

Flagship phones from ~2020 onward are patched.

## Beacon-side signal for AP-side Kr00k

Kr00k is a client-side bug — the AP is not the vulnerable party.
But an AP built on Broadcom/QCA silicon can also exhibit the same
zero-PTK-tail behavior when disassoc'd from a STA's side (AP-side
Kr00k). Fingerprint the AP's chipset via `ap-fingerprinting/`.

## Confirming the vuln without a full attack

- Force a single disassoc against a candidate STA.
- Capture the next 4–8 data frames from that STA on the same channel.
- Try decrypting with an all-zero PTK. If plaintext appears, the
  target is vulnerable.
- ESET released a detector script (see `bibliography.json:
  eset-2020-kr00k-paper`); the flow above is what it automates.

## What "still effective" means in a CTF

A Kr00k puzzle plants a vulnerable client on a target AP. The flag
is in the tail plaintext post-disassoc. If your recon shows an older
Echo / Kindle / camera-class client, this is the puzzle to run.

## Cite

- ESET 2020 Kr00k white paper.
- CVE-2019-15126, CVE-2020-3702.
- knowledge/kr00k/reference.md.
- knowledge/chipsets/reference.md (Broadcom/Cypress/QCA lineage).
- attacks.json: `kr00k-broadcom-cve-2019-15126`,
  `kr00k-qca-cve-2020-3702`.
