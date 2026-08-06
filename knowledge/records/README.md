# P1N3NUT5 typed records

The half of `knowledge/` you *look facts up in* — dated, cited,
region-bound, disputed-aware JSON. Free-text prose lives in
`knowledge/<topic>/*.md` and is what the assistant *reads*; these
records are what the `lookup_*`, `verify_claim`, `explain_attack`,
`bibliography`, `cross_reference`, and `search_records` MCP tools
resolve against.

Phase 0 has authored none of the files below. Phase 2 in
plan-organize.md is where they land. Full schemas and sample records
are in plan-knowledge.md.

## Files (planned)

| file | category | what's in it |
|---|---|---|
| `standards.json` | `standard` | 802.11 amendments (a/b/g/n/ac/ax/be), 802.1X, key EAP RFCs |
| `channels.json` | `band_and_channel` | every 2.4 / 5 / 6 GHz channel — number, center MHz, widths, per-region regulatory status, DFS/TPC |
| `frame_types.json` | `frame_type` | management / control / data / extension types + subtypes, byte offsets, field layout |
| `ies.json` | `information_element` | every IE the assistant will see, with byte layout |
| `security_suites.json` | `cipher` + `key_management` | RSN cipher-suite selectors, AKM selectors, key derivation |
| `eap_methods.json` | `eap_method` | inner/outer, cred type, replay properties, known attacks |
| `attacks.json` | `attack` | preconditions, tools, hashcat mode, mitigation, era_bounds, still_effective_2026, target_security[], transports_needed[] |
| `cves.json` | `cve` | wireless CVEs cross-referenced from `attacks.json` |
| `hashcat_modes.json` | `hashcat_mode` | mode number, capture format, producer tool, example |
| `pineapple_endpoints.json` | `pineapple_endpoint` | every API path + SSH command the MCP invokes, with `firmware_min` / `firmware_max` |
| `openwrt_uci.json` | `openwrt_uci` | UCI section catalog (`network`, `wireless`, `dhcp`, `firewall`, `hostapd`, `pineap`) |
| `defense_and_detection.json` | `defense_and_detection` | PMF/802.11w, WIDS heuristics, deauth-flood detection, evil-twin countermeasures |
| `bibliography.json` | `bibliography` | pinpoint sources — IEEE / RFC / DEFCON / USENIX / GitHub / vendor docs |

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
- Sample `attacks.json` and `security_suites.json` records live in
  plan-knowledge.md (§ "Sample records").
