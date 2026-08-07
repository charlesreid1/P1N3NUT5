# Wi-Fi 7 (802.11be) — MLO

## Multi-Link Operation

One client on 2.4 + 5 + 6 GHz simultaneously via a single association.
The client is now an MLD (Multi-Link Device) with an MLD MAC that
identifies the client across links, plus per-link MACs that identify
the client on each radio band.

Key security consequence: **the PTK is derived once and shared across
all the links.** A single 4-way handshake covers all bands.

## What is new attack-wise (2024–2026 research)

- **Link-desync primitives.** If the attacker can suppress one link
  (RF jam, targeted deauth on a link that isn't PMF-protected on that
  band), the client's per-link state diverges from the AP's. Some
  implementations mishandle the resulting inconsistency.
- **MLD address vs. link address exposure.** A client behind
  randomized per-link MACs still exposes the MLD MAC in some frames.
  Cross-link correlation may re-identify a client that thought MAC
  randomization protected it.
- **Shared-PTK-across-links replay.** Nonce-management across links
  is where a lot of early 2024–2026 research is focused; specifics
  will land as they publish.

## Recognition

- **EHT Capabilities IE (ext ID 108)** in beacons.
- **Basic Multi-Link ML Element** carrying the MLD MAC.

## Cite

- IEEE Std 802.11be-2024.
- attacks.json: `wifi7-mlo-link-desync` (confidence: secondary — a
  frontier area where the corpus expects to update as papers land).
