# WPA2 recognition

First-60-seconds triage. Read the RSN IE.

## Is it WPA2-PSK or WPA2-Enterprise?

AKM Suite List:

- **`00-0F-AC:02`** = PSK — PMK is a passphrase-derived key. Offline
  crack via 4-way or PMKID.
- **`00-0F-AC:01`** = 802.1X — PMK is derived from an EAP inner method.
  Pivot to rogue-RADIUS / cert-phish.
- **Both present** — enterprise + PSK on the same SSID (rare, misconfig).

## Is it WPA2-only or WPA3 transition?

If the RSN IE carries **both** AKM 2 (PSK) **and** AKM 8 (SAE), it's
WPA3 transition mode. A WPA2-capable client can be pushed onto the WPA2
side and captured. See `wpa3/reference.md` and the
`wpa3-transition-downgrade` attack record.

## Does it leak PMKID?

Two ways to check:

1. Passive — capture beacons and check the RSN IE PMKID Count field.
   Many APs advertise 0 in the beacon but include a PMKID in M1.
2. Active — send one association attempt and read M1 with wireshark.
   Look for the PMKID field in the EAPOL-Key IE. If present, you're on
   the Steube 2018 fastpath.

## Is PMF required?

RSN Capabilities bit 6 (MFPR — Management Frame Protection Required)
and bit 7 (MFPC — MFP Capable):

- **0/0** — no PMF. Deauth is unrestricted.
- **0/1** — PMF optional (bit 7 MFPC set, bit 6 MFPR clear). Some
  clients negotiate PMF, some don't. Unicast deauth still works
  against non-PMF clients.
- **1/1** — PMF required. Broadcast deauth is a no-op; unicast is
  authenticated. Pivot to Kr00k (disassoc triggers all-zero PTK on
  vulnerable clients), SSID Confusion, or the WPA3-side (if this is
  actually WPA3-only).

## Cite

- IEEE Std 802.11-2020, §9.4.2.24.
