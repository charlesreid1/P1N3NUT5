# P1N3NUT5

> A WiFi CTF co-pilot for the Hak5 Pineapple Mark VII.

**P1N3NUT5** is the wireless-CTF twin of
[PHR34CKER5](../PHR34CKER5/README.md): a corpus of 802.11 knowledge *and*
a live control surface for the Hak5 WiFi Pineapple Mark VII, both
exposed over the Model Context Protocol (MCP). It knows the domain
(WPA2/WPA3, EAP, PMKID, KRACK, Dragonblood, FragAttacks, WPS, evil twins,
captive portals) and can act on it: drive recon, spin up rogue APs,
capture handshakes, and hand them to hashcat.

## Status

Planning only. Two documents describe what we're building:

- [`plan-organize.md`](plan-organize.md) — repo layout, MCP tool
  surface, and the API-vs-SSH transport split
- [`plan-knowledge.md`](plan-knowledge.md) — the knowledge base: prose
  topics, typed records, bibliography discipline

Nothing under `src/`, `knowledge/`, `skills/`, `scripts/`, `docs/`, or
`tests/` has been authored yet. The plans specify what will land there.

## Three tiers, from knowing to acting

- **Know** — corpus tools (`list_topics`, `search_lore`, `read_lore`,
  `random_lore`) + typed-record lookups (`lookup_standard`,
  `lookup_frame`, `lookup_cipher`, `lookup_attack`, `verify_claim`,
  `explain_attack`)
- **Act** — Pineapple control: recon, PineAP, rogue AP, evil twin,
  deauth, capture, injection. Some via REST API, some via SSH — the
  MCP picks the right transport per capability.
- **Perceive** — pcap parsing, handshake and PMKID extraction, hashcat
  handoff, IE decoding, evil-twin diffing

## Read the plans, then this makes sense

Everything else — the repo map, the tool inventory, the record schemas,
the bibliography, the WCTF playbook — is in the two `plan-*.md` files.
Start with `plan-organize.md`.

## License

MIT (planned).
