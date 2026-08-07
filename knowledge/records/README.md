# P1N3NUT5 typed records

The half of `knowledge/` you *look facts up in* — dated, cited,
region-bound, disputed-aware JSON. Free-text prose lives in
`knowledge/<topic>/*.md` and is what the assistant *reads*; these
records are what the `lookup_*`, `verify_claim`, `explain_attack`,
`bibliography`, `cross_reference`, and `search_records` MCP tools
resolve against.

21 files, ~890 records on disk. Every file is loaded at startup;
per-record depth is locked by `tests/test_depth.py`.

## Files

| file | category | records | what's in it |
|---|---|---|---|
| `standards.json` | `standard` | 31 | 802.11 amendments (a/b/g/n/ac/ax/be), 802.1X, key EAP RFCs |
| `channels.json` | `band_and_channel` | 187 | every 2.4 / 5 / 6 GHz channel — number, center MHz, widths, per-region regulatory status, DFS/TPC |
| `frame_types.json` | `frame_type` | 40 | management / control / data / extension types + subtypes, byte offsets, field layout |
| `ies.json` | `information_element` | 86 | every IE the assistant will see, with byte layout |
| `security_suites.json` | `cipher` + `key_management` | 33 | RSN cipher-suite selectors, AKM selectors, key derivation |
| `eap_methods.json` | `eap_method` | 30 | inner/outer, cred type, replay properties, known attacks |
| `attacks.json` | `attack` | 98 | preconditions, tools, hashcat mode, mitigation, era_bounds, still_effective_2026, target_security[], transports_needed[] |
| `cves.json` | `cve` | 42 | wireless CVEs cross-referenced from `attacks.json` |
| `hashcat_modes.json` | `hashcat_mode` | 30 | mode number, capture format, producer tool, example |
| `pineapple_endpoints.json` | `pineapple_endpoint` | 49 | every API path + SSH command the MCP invokes, with `firmware_min` (100% coverage) |
| `openwrt_uci.json` | `openwrt_uci` | 40 | UCI section catalog (`network`, `wireless`, `dhcp`, `firewall`, `hostapd`, `pineap`) |
| `defense_and_detection.json` | `defense_and_detection` | 25 | PMF/802.11w, WIDS heuristics, deauth-flood detection, evil-twin countermeasures |
| `bibliography.json` | `bibliography` | 45 | pinpoint sources — IEEE / RFC / DEFCON / USENIX / GitHub / vendor docs |
| `chipset_vulns.json` | `chipset_vuln` | 15 | per-chipset CVE mapping — Broadcom Kr00k, QCA variant, MediaTek WPS |
| `client_fingerprints.json` | `client_fingerprint` | 20 | IE-order + capability-bits signatures per stack |
| `default_psks.json` | `default_psk` | 15 | vendor default-PSK derivation catalog (UPC, Sky, BT, Technicolor …) |
| `dos.json` | `dos` | 16 | deauth flood, beacon flood, CTS storms, RF DoS |
| `karma_family.json` | `karma_attack` | 10 | Karma / Karmetasploit / MANA / PineAP variants |
| `local_operations.json` | `local_operation` | 11 | offline tools the MCP wraps that never touch the Pineapple |
| `roaming.json` | `roaming` | 15 | 802.11r/k/v/OKC/FT flows |
| `vendors.json` | `vendor` | 6 | vendor-lockout / firmware-EOL data |

## Record shape (mirrors PHR34CKER5)

```json
{
  "id": "kebab-case-unique",
  "name": "human name",
  "aliases": ["other names"],
  "category": "attack | cipher | eap_method | ...",
  "region": "universal | US | EU | JP | ...",
  "era_bounds": ["2018-08-04", null],
  "still_effective_2026": true,
  "confidence": "primary | secondary | community | folklore",
  "citations": ["bib-id", "..."],
  "see_also": ["other-record-id"],
  "disputed": { "field": "why disputed + competing values" },
  "technical_body": { ... },
  "preconditions": [ ... ],
  "tools": ["hcxdumptool", "hashcat"],
  "transport": "ssh | api | analysis"
}
```

## Discipline (enforced at load time)

- `citations[]` **must** be non-empty; every entry resolves to a
  `bibliography.json` id. Loader raises on violation.
- `era_bounds` is `[first_effective, last_effective]`; either end may
  be `null`. `explain_attack` refuses when caller-specified era lies
  outside the bounds — but returns steps by default (WCTF ethos).
- `still_effective_2026` distinguishes techniques that are gone from
  techniques whose *targets* are gone but whose *technique* still works
  where the target survives.
- `confidence` weighting matches PHR34CKER5:
  `primary` (IEEE/IETF/vendor spec)
    > `secondary` (DEFCON talk with released code, USENIX paper)
    > `community` (blog, GitHub README, hallway con)
    > `folklore` (unverified claim, tribal knowledge).
- `disputed` is never silently resolved — surface both values with
  provenance and let `verify_claim` return `needs_qualification`.

## Envelope

Every KR tool response carries:

```json
{
  "citations": ["..."],
  "era_bounds": ["...", null],
  "region": "...",
  "confidence": "primary|secondary|community|folklore"
}
```

## Adding records

- Hand-authored. No web-scrape auto-generation. Every record
  hand-verified against a primary or secondary source.
- Add or update entries under `bibliography.json` first, then reference
  their ids in new records. The loader will fail otherwise.
- Depth floors in `tests/test_depth.py` are the load-bearing acceptance
  gate: attacks need `flag_signature`, `mitigation`, ≥2 preconditions,
  ≥2 tools; frames need non-empty `fields[]`; IEs need non-empty
  `layout[]`; hashcat modes need `example_command`.
