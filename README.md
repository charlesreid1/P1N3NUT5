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

Both halves ship. The **acting half** — `src/p1n3nut5_mcp/` — is ~3,400
LOC of MCP code: transport (API + SSH), recon + PineAP + filter tools,
perception (pcap parsing, handshake / PMKID extraction, hashcat handoff),
attack primitives (deauth, capture, rogue AP, evil twin), and
`run_sequence` orchestration. The **knowing half** — `knowledge/` — is
55 topic dirs / ~164 markdown files plus 21 typed JSON record files
with ~890 records total, all loaded and searchable. 857 tests pass
against injected fake transports in under a second; no live radio
needed in CI.

Per-file record floors — locked by `tests/test_depth.py` so the depth
can't silently regress:

| file                 | floor | current |
| -------------------- | ----- | ------- |
| `attacks.json`       | 90    | 98      |
| `frame_types.json`   | 30    | 40      |
| `ies.json`           | 80    | 86      |
| `eap_methods.json`   | 30    | 30      |
| `hashcat_modes.json` | 30    | 30      |
| `local_operations.json` | 11 | 11      |

`pineapple_endpoints.json` has `firmware_min` on every entry (100%
coverage). `verify_claim` ships with a 22-pattern trap catalog for
adversarial claims (SSID Confusion, PMF-stops-deauth, WPA3-fixes-offline,
hidden-SSID-is-secret, PMKID-always-leaks, MAC-randomization-stops-
tracking, and so on).

## Three tiers, from knowing to acting

- **Know** — corpus tools (`list_topics`, `search_lore`, `read_lore`,
  `random_lore`) + typed-record lookups (`lookup_standard`,
  `lookup_frame`, `lookup_cipher`, `lookup_attack`, `verify_claim`,
  `explain_attack`, `lookup_hashcat_mode`, `lookup_cve`, `bibliography`,
  `cross_reference`, `search_records`)
- **Act** — Pineapple control: recon, PineAP, rogue AP, evil twin,
  deauth, capture, injection. Some via REST API, some via SSH — the
  MCP picks the right transport per capability.
- **Perceive** — pcap parsing, handshake and PMKID extraction, hashcat
  handoff, IE decoding, evil-twin diffing

## Quickstart

Start with [`docs/pineapple_setup.md`](docs/pineapple_setup.md) —
first-time-through: prereqs, env vars, install line, smoke test. Then
[`docs/wctf_playbook.md`](docs/wctf_playbook.md) for the operator-facing
playbook once the device is talking. The
[`skills/pineapple/SKILL.md`](skills/pineapple/SKILL.md) file is what
the assistant loads at session start.

## License

MIT (planned).
