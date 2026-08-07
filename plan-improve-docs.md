# PLAN — close the depth gaps in the knowledge base

> Status: **plan only, work not started.** Sibling to `plan-organize.md`
> and `plan-knowledge.md`; read those first. This file lays out what
> Phase 7h *didn't* finish. The corpus is at target on head counts but
> below the plan's stated acceptance criteria on record depth. Below is
> a per-file punch list and the order in which to close it.

## Why this exists

`plan-knowledge.md §Acceptance criteria` sets a bar — every `attacks.json`
record has `preconditions`, `tools`, `mitigation`, `era_bounds`,
`still_effective_2026`, `hashcat_mode` (or explicit null), a
`flag_signature`, and at least one primary/secondary citation; every
`security_suites.json` record round-trips through schema validation with
numeric-field completeness; every `pineapple_endpoints.json` record has
both `firmware_min` and at least one of `api` or `ssh` populated. The
loader is validator-clean and citations resolve, but a spot-check of
per-record content shows several files hit the head-count target with
schema-legal but content-thin records. The gap is closable in a single
depth pass; this file scopes it.

## Guiding rule — deepen, don't add

**No new records; no new topics; no new prose files.** The head counts
match the plan already, and adding more records dilutes the "every
record earns its keep" discipline PHR34CKER5 established. Every task
below is a **fill-in** against records that already exist, or a schema
refinement against a category whose acceptance test didn't match the
authored shape.

Exception: when the depth pass reveals that a promised slug from
Appendix B is missing entirely (see §attacks.json below), add a record
for that slug — but only for slugs the plan explicitly named.

## The audit

Spot-checked 2026-08-07 by re-reading `plan-knowledge.md` acceptance
criteria against actual record content. Full audit lives in the
session that produced this file; the gaps below are the load-bearing
misses.

### attacks.json — the load-bearing file, thinnest content per record

**Head count:** 90/90 (target 90). **Depth:** ~30% by acceptance criteria.

| field | populated | target | gap |
| ----- | --------- | ------ | --- |
| `flag_signature` | 28/90 | 90/90 | 62 records missing |
| `mitigation` | 14/90 | 90/90 | 76 records missing |
| `notes` (context) | 28/90 | most Tier-1 + Tier-1.5 | ~50 records missing |
| `preconditions` (≥2 bullets) | 29/90 | most | 61 records at 1 bullet |
| `tools` (≥2 bullets) | 31/90 | most | 59 records at 1 bullet |

Frontier records (`wifi7-mlo-link-desync`, `macstealer-mac-hijack`,
`twt-forced-sleep-abuse`, `ru-based-ofdma-dos`) are the thinnest —
schema-legal one-liners. The plan explicitly calls out frontier records
as needing *equal or greater weight* than legacy hits.

**Missing Appendix-B slugs (11):**

- `pmk-crack-mask-attack`, `pmk-crack-hybrid` — cracking-tradecraft
  variants; Appendix B names them, corpus doesn't have them
- `tim-dtim-poison` — Appendix B names it under DoS; corpus has
  `dos.json` entries but no `attacks.json` record
- `snoopy-track` — Appendix B karma-family; corpus has
  `karma_family.json:snoopy` but no attack record
- `broadpwn-broadcom-cve-2017-11120` — corpus has chipset-vuln + prose,
  no attack record
- `realtek-rtl87xx-cve-2021-28492` — same story
- `scapy-crafted-beacon-with-vendor-stego` — Appendix B; corpus has
  `beacon-stego-vendor-ie` but not this named companion record
- Renames that are fine but should be documented in the record's
  `aliases`: `kr00k-qualcomm-cve-2020-3702` ↔ `kr00k-qca-cve-2020-3702`,
  `frame-injection-arbitrary` ↔ `packet-inject-arbitrary`
- `pmk-crack-hashcat` — likely subsumed by `wpa2-4way-capture` +
  `pmkid-capture`; either add a wrapper record or note the subsumption
- `krack-ap-key-reinstall` — Appendix B lists it distinct from the
  client-side variant; corpus only has the client one

**Task A1 — flag_signature pass.** For all 62 attacks missing
`flag_signature`, add one string: "what does the WCTF flag look like if
this attack lands." One sentence. Reuse the existing 28 as tonal
anchors — `pmkid-capture` says "PSK is the flag"; `evil-twin-clone`
says "victim client connects to your BSSID; capture its traffic or
serve a captive portal." No attack ships without one; if a record
genuinely has no WCTF-flag shape (DoS primitives, some frame-injection
utilities), set `flag_signature: null` explicitly so the field is
present.

**Task A2 — mitigation pass.** For the 76 attacks missing `mitigation`,
add a 1–3-bullet list: what stops or blunts this attack. Draw from the
existing prose (`recognition.md` files usually name the defense) and
the `defense_and_detection.json` records. Cross-reference with
`see_also` where a defense record already exists.

**Task A3 — preconditions and tools depth.** For the 61 records at
`preconditions < 2` and 59 at `tools < 2`, expand to at least 2 bullets
each. Preconditions should include *both* the target property (e.g.
"target uses WPA2-PSK") *and* the operational property (e.g. "a client
is present and (re)associating"). Tools should be the actual chain
(capture → convert → crack), not just the last step.

**Task A4 — frontier record notes.** For every Tier-1.5 attack record
(kr00k-*, ssid-confusion-*, framing-frames-*, macstealer-*,
wifi7-mlo-*, ft-*, mc-mitm-*, twt-*, rnr-*, ru-*), add a `notes` field
that names the paper, the vulnerability year, and the "why this hits
in 2026" reason. Frontier records need the paper title in `notes`
because the citation id (e.g. `vanhoef-ssid-confusion-2024`) is opaque
to a reader.

**Task A5 — missing Appendix-B slugs.** Add the 8 truly missing records
(the 3 aliasable renames don't need new records — just update
`aliases[]` on the existing entry). Author with the same acceptance
criteria as the depth pass — every new record must land at full depth,
not stub depth.

### frame_types.json — 0/40 records carry byte layouts

Plan says: "byte offsets, field layout." Actual: every record has
`technical_body.purpose` (a sentence) and `wctf_uses` (a list), which
is genuinely useful but is not the spec-grade content `lookup_frame`
was designed to return. The load-bearing detail (e.g. the 26-byte
deauth frame layout the plan calls out) lives in prose (`wpa2/reference.md`,
`deauth/reference.md`) but not in the record.

**Task F1 — byte layout per frame type.** Add
`technical_body.fields[]` to each record — a list of
`{name, offset_bytes, length_bytes, notes}`. For 26-byte deauth this
is exactly the ASCII table the plan references. For beacon (variable
length), enumerate the fixed part (12 bytes: timestamp, beacon interval,
capability info) plus a note that IEs follow. Reference
`ies.json` records by `id` for IE contents (don't duplicate).
Priority order: management subtypes first (beacon, probe req/resp,
auth, assoc, deauth, disassoc, action), then EAPOL-Key, then control
and data types. Reference: IEEE 802.11-2020 §9.

**Task F2 — `wctf_uses` for the remaining subtypes.** Roughly
half the frame records have `wctf_uses`; extend the missing half so
`lookup_frame` returns a consistent shape.

### ies.json — 1/80 records carry byte layouts

Same shape as frame_types: `technical_body` gives `element_id`,
`appears_in`, and a one-line `contents:` string. Plan asks for "byte
layout per IE."

**Task I1 — layout per IE.** For each IE record, add
`technical_body.layout[]` as a list of
`{name, offset_bytes, length_bytes, notes}`. Prioritize the IEs an
attacker actually parses: SSID (0), Supported Rates (1), DS Parameter
Set (3), TIM (5), Country (7), RSN (48), HT/VHT/HE/EHT Capabilities,
WPS (Vendor-Specific 221 OUI 00-50-F2), Interworking (107), RNR (201),
MDE (54), MLD Basic. Non-priority IEs can carry a truncated
`layout: [{name: "opaque", notes: "see IEEE 802.11-2020 §9.4"}]`
placeholder so the schema is uniform.

**Task I2 — missing frontier IEs.** ANQP elements are not first-class
records — `ie-interworking` references them in prose but there's no
`ie-anqp-nai-realm`, `ie-anqp-roaming-consortium`, `ie-anqp-venue-info`
record. Plan §Ontology explicitly lists ANQP under
`information_element`. Add ~6 ANQP-element records so `hotspot2-anqp-flag`
in `ctf/` has typed records to link to.

**Task I3 — rename normalization.** The plan uses `ie-mde` and
`ie-anqp`; the corpus uses `ie-mobility-domain` and (nothing for
ANQP). Either add the shorter slugs as `aliases`, or rename. Prefer
`aliases[]` so existing cross-references keep resolving.

### eap_methods.json — 0/30 have the `attacks[]` back-reference the plan required

Plan §Layer 3 authoring order, step 11: "eap_methods.json **second
pass** — now that attacks.json exists, fill in each EAP method's
`attacks[]` back-references." This second pass never ran. Records have
`technical_body.known_flaws` as a string list, which is a partial
substitute, but a WCTF operator asking `lookup_eap(peap)` should get
back the actual `attacks.json` ids (`eap-inner-downgrade-peap-mschapv2`,
`cert-phish-eaphammer-weak-validation`, etc.) so cross-navigation
works.

**Task E1 — `attacks[]` on every EAP method.** For each of 30 records,
add `attacks[]` — a list of `attacks.json` ids where the attack has
that method in its `target_security` or where the method is named in
the attack's prose. Load-bearing pairs:
- `eap-md5` → `eap-md5-offline-brute` (add if not present) or wrap the
  challenge/response bullet from `known_flaws` into an attack record
- `eap-leap` → `leap-legacy-crack`, `asleap-mschapv2-crack`
- `eap-peap-mschapv2` → `eap-inner-downgrade-peap-mschapv2`,
  `mschapv2-challenge-response-capture`, `hashcat-5500-mschapv2-crack`,
  `rogue-radius-hostapd-wpe`
- `eap-peap-gtc` → `eap-inner-downgrade-peap-gtc`,
  `eap-gtc-plaintext-token-capture`
- `eap-ttls-pap` → `rogue-radius-eaphammer` (plaintext-password path)
- `eap-pwd` → `dragonblood-sidechannel`, `dragonblood-timing`
- `eap-tls`, `eap-tls-1-3` → `cert-phish-eaphammer-weak-validation`
- `eap-fast-mschapv2` → PEAP-MSCHAPv2 chain

### hashcat_modes.json — 0/30 have example commands

Plan asks for "mode number, capture format, source tool, **example
command**." Records have `technical_body.example_line` (the hash-line
format) but not `example_command` (the CLI). A WCTF operator asking
`lookup_hashcat_mode(22000)` should get back a runnable snippet.

**Task H1 — example CLI per mode.** For each of the 30 records, add
`technical_body.example_command` — a one-line shell invocation with
the mode number, a placeholder hash path, and a placeholder wordlist.
For mode 22000, this is
`hashcat -m 22000 hashes.22000 rockyou.txt -w 4 --status`. For mode
5500, `hashcat -m 5500 mschapv2.txt rockyou.txt`. Etc. Placeholders
are fine — the operator will substitute paths.

**Task H2 — key renames for schema consistency.** The plan uses
`producer_tool` / `source_tool`; the corpus uses `producer`. Add
`producer_tool` as an alias field or rename. Same problem as ies.json
renames; prefer additive.

### pineapple_endpoints.json — 11/60 missing firmware_min

Plan acceptance: "100% of pineapple_endpoints.json records have both
firmware_min and at least one of api or ssh populated." The 11 that
fail are all *local-host* operations (parse_pcap, extract_handshakes,
convert_to_hashcat, crack_start/status/stop/result, decode_ies,
beacon_diff, client_fingerprint, call_log, run_sequence). They are
not device endpoints — they run in the MCP process against a
downloaded pcap.

Two options:

**Task P1a — carve out local operations from `pineapple_endpoints.json`.**
Move these 11 records to a new `local_operations.json` (category
`local_operation`) so the endpoint file's acceptance test can pass at
100%. This is the cleaner fix but adds a file.

**Task P1b — mark them explicitly.** Add
`transport: "analysis"` and `firmware_min: null` (with a schema-level
allowance for local operations), leaving them in
`pineapple_endpoints.json`. This preserves the "one place to find
every MCP-exposed capability" property but bends the acceptance
criteria.

Recommend P1a — the plan already uses `transport: "analysis"` as a
first-class value in the tool envelope; the record file split makes
that explicit. Update `plan-knowledge.md` §Records ontology table to
add the row.

### security_suites.json — 33/33 pass numeric acceptance already

This one's clean. Full depth on all 33. Included in the audit only to
confirm the "channels.json + security_suites.json" pair meets the
plan's numeric-completeness bar. No task.

### channels.json — 187/187 pass regulatory acceptance

Also clean. All records have `regulatory` per US/EU/JP; 6 GHz records
have the WPA3-only note. No task. The staged diff (98 → 187) adds
bonded-channel records (40/80/160/320 MHz) and was in-flight when this
audit ran — commit that first, then this file is settled.

### Prose corpus stubs — the two Tier-1.5 macstealer files

Plan §Acceptance criteria: "Every Tier 1.5 (frontier) topic ships with
a walkthrough.md even if the walkthrough is 5 lines." The current
`macstealer/walkthrough.md` is 5 lines. That meets the letter of the
acceptance criterion, but the *reference* file is a single paragraph
with no attack shape / IE decode / decrypt path. This is a Tier-1.5
frontier attack that DEFCON WCTF 2026 organizers are likely to
weaponize; underweight it and the assistant will fumble the puzzle.

**Task S1 — deepen `macstealer/reference.md`.** Bring it to the same
shape as `ssid-confusion/reference.md`: the CVE, the primitive at the
byte level (which client-side check fails), the affected implementations
as of 2026, one paragraph on how it composes with SSID Confusion and
Framing Frames.

**Task S2 — deepen `macstealer/walkthrough.md`.** Add a
worked-example section with actual MAC-hijack commands, a failure-modes
block, and a WCTF flag-shape paragraph.

## Coverage tests we should add

The head-count tests catch missing records but not shallow ones. Add:

**Task T1 — depth test for `attacks.json`.** A pytest that asserts
`flag_signature`, `preconditions` (≥2), `tools` (≥2), `mitigation`
(≥1 or explicit null) on every record. This is the "acceptance
criteria in CI" pattern PHR34CKER5 uses; it prevents the corpus
from silently regressing on depth after we do the pass.

**Task T2 — layout test for `frame_types.json` and `ies.json`.**
Assert every record's `technical_body` has either a non-empty
`fields[]`/`layout[]` array or an explicit `layout: [{name: "opaque"}]`
placeholder. Placeholders count so IEs the corpus doesn't need to
decode aren't blocked, but the schema stays uniform.

**Task T3 — back-reference test for `eap_methods.json`.** Assert every
record has a non-empty `attacks[]` and every id resolves to an
`attacks.json` id.

**Task T4 — example-command test for `hashcat_modes.json`.** Assert
`technical_body.example_command` is present and non-empty.

**Task T5 — acceptance-criteria roll-up test.** One test that reads
this plan's acceptance targets from a small JSON manifest and asserts
each target. Makes the criteria versionable; a plan change is a
committed test change.

## Suggested execution order

Do these in-order — each phase leaves the corpus in a validator-clean,
test-green state, so stopping between them is fine. The prior work in
`plan-knowledge.md` §Authoring order gives the layered dependency; this
plan's execution order respects it (attack-side depth before eap-side
back-references before eap-side tests, etc.).

**Phase D1 — attacks.json depth.** Tasks A1–A5. Load-bearing;
everything else refers back. Land the flag_signature + mitigation
pass first (mechanical), then the frontier-notes + preconditions/tools
depth (judgment-heavy), then the missing Appendix-B slugs.

**Phase D2 — frame_types.json + ies.json byte layouts.** Tasks F1, F2,
I1, I2, I3. These are independent of D1 and can run in parallel with
it, but wait until the loader test T2 exists so wrong-shape entries
fail loudly.

**Phase D3 — eap_methods.json back-references.** Tasks E1. Must come
after D1 because the attack records need to exist first.

**Phase D4 — hashcat_modes.json example commands + endpoint carve-out.**
Tasks H1, H2, P1a. Independent of everything else. Do the endpoint
carve-out as one atomic commit so the ontology table in
`plan-knowledge.md` updates in the same change.

**Phase D5 — macstealer prose deepening.** Tasks S1, S2. Small,
self-contained. Do last so the deepening happens against a corpus
whose `attacks.json` and `ies.json` already deepened; the walkthrough
can cite the deepened records.

**Phase D6 — depth-test CI.** Tasks T1–T5. Run last; each task locks
in the depth we authored in D1–D5.

## Non-goals for this depth pass

- **No new topics or records beyond the 8 named-in-plan slugs.** The
  corpus is at target; adding more without a plan-driven reason is
  drift.
- **No prose corpus rewrites.** Individual walkthroughs shorter than
  the depth bar aren't wrong — the plan says "even if the walkthrough
  is 5 lines." macstealer is the only cited exception.
- **No test coverage beyond the depth tests.** Gold + adversarial
  corpora are at target counts and structured. Adding more without a
  new puzzle surface is churn.
- **No schema breaking changes.** Every new field is additive; every
  rename lands as an alias. The loader keeps loading current records
  without migration.

## Acceptance criteria for the depth pass

- 100% of `attacks.json` records have `flag_signature` (string or
  explicit null), `mitigation` (≥1 bullet or explicit null with
  citation), `preconditions` (≥2), `tools` (≥2).
- 100% of `frame_types.json` records have `technical_body.fields[]`
  non-empty (or `[{name:"opaque"}]` for out-of-scope subtypes).
- 100% of `ies.json` records have `technical_body.layout[]`.
- 100% of `eap_methods.json` records have `attacks[]` non-empty, each
  id resolving to `attacks.json`.
- 100% of `hashcat_modes.json` records have
  `technical_body.example_command`.
- Local operations moved out of `pineapple_endpoints.json` (or
  explicitly exempt) so its 100%-firmware_min acceptance passes.
- `plan-knowledge.md` §Records ontology reflects the endpoint / local
  split.
- All existing tests still pass; new depth tests all pass; gold +
  adversarial corpora unchanged.
- Corpus stays validator-clean: 0 broken citations, 0 broken
  `see_also`.
