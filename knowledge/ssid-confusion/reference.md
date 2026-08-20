# SSID Confusion — the 4-way handshake does not authenticate the SSID

CVE-2023-52424, Héloïse Gollier & Mathy Vanhoef 2024 (KU Leuven /
DistriNet), co-disclosed 2024-05-14. The 802.11-2020 PTK derivation
mixes the PMK, both nonces, and both MAC addresses — but not the SSID.
An attacker who controls two networks with the same PSK can convince a
client that it is on network X while the client is actually associated
to network Y.

## Why this matters

- **VPN auto-connect bypass.** VPN products that toggle on/off based on
  "am I on the CorpWiFi SSID?" trust a value that isn't cryptographically
  bound to anything in the session.
- **Trust-on-SSID heuristics.** Enterprise MDM policies that whitelist
  behavior per-SSID trust the wrong signal.
- **Not a plain evil twin.** The attacker doesn't need to guess the PSK
  or crack anything. They need two SSIDs the client already trusts to
  share a PSK — which happens often on rollover networks, guest+staff
  networks with a shared password, or by design in some captive setups.

## Preconditions

- Attacker controls the two networks (or one legitimate AP the client
  trusts, and a rogue with a matching PSK on the other SSID).
- Both networks use the same PSK / same EAP credentials.
- Client has both SSIDs in its preferred-network list.

## Mitigation status (2026)

The standards fix — including the SSID in the 4-way — has been proposed
but is not universally deployed. Client-side heuristics (rejecting
association to an SSID whose beacon-declared MAC doesn't match the
address in the 4-way response) are the dominant deployed mitigation.
Per-OS status varies; check the specific client.

## Cite

- Héloïse Gollier and Mathy Vanhoef, "SSID Confusion: Making Wi-Fi
  Clients Connect to the Wrong Network" (2024, KU Leuven / DistriNet).
  CVE-2023-52424, co-disclosed 2024-05-14 (Top10VPN co-disclosure).
- IEEE Std 802.11-2020 §12.7 (the section that famously omits SSID
  from PTK derivation).
