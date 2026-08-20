# Wi-Fi 7 (802.11be) — MLO

## Multi-Link Operation

One client on 2.4 + 5 + 6 GHz simultaneously via a single association.
The client is now an MLD (Multi-Link Device) with an MLD MAC that
identifies the client across links, plus per-link MACs that identify
the client on each radio band.

Key security consequence: a single 4-way handshake covers all bands,
but the per-link key material is **not** literally shared —
per 802.11be-2024 §12.7.1.9.4:

```
Wi-Fi 7 MLO keying (802.11be-2024 §12.7.1.9.4):

- **PMK** — derived once, shared across links in the ML setup.
- **PTKSA** — one per link. Each link's PTK is derived with its own
  MAC pair (link MAC A ↔ link MAC B), so PTKs differ per link.
- **PN counters** — per-link, per-key. Cross-link nonce reuse is
  prevented by the different derivation.
- **MLO group keys (MLO GTK / MLO IGTK)** — MLD-scoped, delivered
  in the ML 4-way and used across all links of the MLD.
```

Common misreading (the earlier version of this doc): "the PTK is
derived once and shared across all links." **Wrong.** The PMK is
shared; each link maintains its own PTKSA with its own PN counters
and its own PTK derived from the shared PMK plus the link's MAC pair.
Only the MLO GTK / MLO IGTK are literally MLD-scoped.

## What is new attack-wise (2024–2026 research)

- **Link-desync primitives.** If the attacker can suppress one link
  (RF jam, targeted deauth on a link that isn't PMF-protected on that
  band), the client's per-link state diverges from the AP's. Some
  implementations mishandle the resulting inconsistency.
- **MLD address vs. link address exposure.** A client behind
  randomized per-link MACs still exposes the MLD MAC in some frames.
  Cross-link correlation may re-identify a client that thought MAC
  randomization protected it.
- **Cross-link PN / replay-window abuse.** PTKs are per-link but the
  PMK and MLO GTK/IGTK are MLD-scoped; the research area is around
  implementations that either (a) reuse a link's PTK on the wrong
  link, or (b) mishandle the MLO group-key PN window when link
  states diverge. Specifics will land as they publish.

## Recognition

- **EHT Capabilities IE (ext ID 108)** in beacons.
- **Basic Multi-Link ML Element** carrying the MLD MAC.

## Cite

- IEEE Std 802.11be-2024.
- attacks.json: `wifi7-mlo-link-desync` (confidence: secondary — a
  frontier area where the corpus expects to update as papers land).
