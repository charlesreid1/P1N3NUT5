# chipsets — reference

Silicon-specific behavior on both sides of the air. The corpus tracks
this as `chipset_vulns.json`; this dir is the operational companion —
what a driver's real behavior looks like at attack time, per family.

Two axes: **attacker-side** (does this adapter do monitor + injection
well?) and **target-side** (does this device have a Kr00k / Broadpwn /
KRACK-class flaw in its silicon or driver?).

## AP-side driver families

### Atheros (ath9k / ath10k / ath11k)

- **ath9k** (802.11n and older) — reliable monitor+injection, works
  with aircrack-ng out of the box. Both Pineapple Mk VII radios are
  ath9k on 2.4 GHz; wlan1 is ath10k on 5 GHz.
- **ath10k** (802.11ac) — firmware-driven; monitor mode works but
  packet injection has quirks (some frames silently rewritten by
  firmware; some driver versions strip the RadioTap header on inject).
- **ath11k** (Wi-Fi 6/6E) — modern, upstream driver; 6 GHz support
  since kernel 5.13, but adapter availability limited.

### Broadcom / Cypress

- **BCM43xx family** — historically the biggest attack surface.
  Broadpwn (CVE-2017-11120), Kr00k (CVE-2019-15126). Cypress
  inherited these when they spun out.
- **BCM43602, BCM4359, BCM4375** — flagship phone silicon; core
  Kr00k CVE largely patched by 2020 but IoT/embedded uses linger.
- **BCM4335, BCM4339** — older; still deployed on IoT (Ring, Wyze,
  first-gen Echo Dot).

### Qualcomm Atheros / QCA

- **QCA61x4A / WCN3990 / WCN6855** — Qualcomm-brand silicon in
  phones. QCA Kr00k variant (CVE-2020-3702).
- **IPQ40xx / IPQ80xx** — SoC-side, ships in most enterprise APs
  post-2018. FragAttacks-relevant firmware.

### MediaTek

- **MT7601 / MT7610** — legacy 2.4 GHz USB adapters. mt76 driver
  well-supported.
- **MT7612U** — dual-band, monitor+injection reliable. Popular in
  Alfa AWUS036ACM.
- **MT7921** — Wi-Fi 6; upstream mt76 driver. Some 6 GHz support in
  2024+ kernels.
- **MT7996** — Wi-Fi 7. Early adopter silicon; driver maturing.

### Realtek

- **RTL8188EU / RTL8188CU** — legacy; monitor works, injection
  variable. Cheap USB dongles.
- **RTL8812AU / RTL8812BU** — dual-band; needs
  `rtl8812au-dkms` on many kernels. Injection works.
- **RTL8814AU** — MU-MIMO. Long-time driver stability issues.
- **RTL87xx family** — CVE-2021-28492 stack overflows.

### Intel iwlwifi

- **AX200 / AX201 / AX210 / AX211** — modern; good client, poor
  attacker card. Monitor mode limited; injection generally unsupported
  on many revs.
- **AX411** — Wi-Fi 7. Same story.

## Client-side chipset fingerprinting

Beacon + probe-request IE order + OUI give away the client's
silicon. The `client_fingerprints.json` records enumerate signatures.

Common families you'll see at DEF CON:

- **Apple (iPhone/iPad/Mac)** — Broadcom historically, Apple silicon
  chain post-2020 (BCM inheritance in modem/WiFi combo chips). iOS
  14+ probes are distinctive.
- **Samsung phones** — Broadcom or Qualcomm depending on model.
- **Pixel phones** — Qualcomm.
- **Windows laptops** — mostly Intel iwlwifi.
- **Older Android** — mix of Broadcom, Qualcomm, MediaTek.
- **IoT (Wyze, Ring, Echo Dot, Kindle)** — heavy Broadcom /
  Cypress; the Kr00k target set.

## Vulnerability cross-reference

- **Kr00k CVE-2019-15126** → Broadcom/Cypress BCM43xx, older
  generations. `chipset_vulns.json`, `attacks.json:kr00k-broadcom-*`.
- **Kr00k CVE-2020-3702** → Qualcomm QCA variant.
- **Broadpwn CVE-2017-11120** → Broadcom BCM4335/BCM4339 on iOS 9/10
  and some Android. RCE from the air.
- **Realtek RTL87xx CVE-2021-28492 family** — several stack overflows
  in the driver + firmware.
- **Cypress firmware bugs** — inherited from Broadcom lineage; some
  additional advisories 2020–2022.

## Cite

- kernel.org linux-wireless driver matrix.
- Cypress security advisories (semiconductor.com/psirt).
- Qualcomm PSIRT advisories.
- Broadcom vendor documentation.
- chipset_vulns.json — 15 records, each with silicon-generation notes.
- cves.json — each CVE mapped to affected silicon.
