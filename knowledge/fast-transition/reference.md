# Fast Transition (802.11r) + 11k / 11v — attack surface

## 802.11r — Fast BSS Transition

Purpose: minimize reassociation latency when a client roams between
BSSIDs in the same Mobility Domain. Instead of running a full 4-way
handshake at the new AP, the client presents a PMK-R1 that both APs
share by virtue of a common PMK-R0.

The key hierarchy:

```
PMK  ──►  PMK-R0  ──►  PMK-R1  ──►  PTK
         (per MDID)   (per BSSID)  (per roam)
```

## Attack surfaces

1. **FT-handshake capture.** The FT reassociation carries an
   M1-analogue that includes a PMKID-shaped value derived from
   PMK-R1. hashcat mode 22000 handles this format. Capture a roam,
   crack the PSK offline. See `attacks.json:ft-handshake-capture`.

2. **PMK-R0 fleet-sharing.** Misconfigured 11r deployments share
   PMK-R0 across many BSSIDs. One PSK crack from one FT roam
   compromises the whole mobility domain.

3. **KRACK against FT reassoc.** CVE-2017-13082 — replaying an FT
   Reassociation Request causes the AP to reinstall the PTK.

4. **hostapd FT source-address spoof (CVE-2019-16275).** hostapd
   pre-2.10 accepted FT Reassociation frames whose transmitter MAC
   (Address 2) did not match the frame's source association. An
   on-network attacker could push a crafted FT reassoc under any
   legitimate STA's identity and shift that STA's session state.
   Not a PSK crack — a session hijack primitive on FT-enabled
   deployments running old hostapd.

## Recognition — is this AP FT-capable?

Look for the **Mobility Domain Element (MDE, IE 54)** in the beacon.
Present → this AP participates in an FT domain. The MDE also carries
the FT Capability field indicating over-the-air vs over-the-DS.

## 802.11k — Neighbor Reports

Purpose: help clients choose a better BSSID to roam to. AP hands out
a list of neighbor BSSIDs with channel and RSSI hints.

Attack: **crafted Neighbor Report action frame** naming your rogue
BSSID as an attractive neighbor. See
`attacks.json:neighbor-report-spoof`.

## 802.11v — BSS Transition Management (BTM)

Purpose: AP asks the client to roam to a specific BSSID. Sent as an
Action frame ("BTM Request").

Attack: **crafted BTM Request** from a rogue AP telling the client
to migrate to the attacker's BSSID. Some vendors' BTM Request handling
does not require PMF authentication on the action-frame category. See
`attacks.json:btm-forced-roam`.

## Cite

- IEEE Std 802.11-2020 §12.11 (FT), §11.10 (Radio Measurement, 11k),
  §11.24 (BSS Transition Management, 11v).
- Vanhoef & Piessens 2017 — KRACK, on FT reassoc replay.
- CVE-2017-13082 (KRACK FT variant); CVE-2019-16275 (hostapd FT
  source-address spoof).
