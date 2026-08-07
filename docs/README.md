# docs/

Long-form guides. Distinct from `knowledge/` — `knowledge/` is
zine-flavored, cited, historically-aware corpus material the MCP
serves as resources; `docs/` is operator documentation for humans
using the tool.

Same shape as PHR34CKER5's `docs/`. The tool-orchestration side ships
in `skills/pineapple/SKILL.md`; the guides below are the longer-form
operator material.

## Guides

### First-time-through

- **[`pineapple_setup.md`](pineapple_setup.md)** — first-time-through
  walkthrough: unbox, factory reset, laptop USB-tether at
  `172.16.42.1`, admin bootstrap, bearer token retrieval, SSH key
  upload, env-var table, install line, and both-transports smoke test.

### In-engagement reach-fors

- **[`cheatsheet.md`](cheatsheet.md)** — one page, tape to the box.
  The 20 tool calls you type most, in the order you type them, plus
  the mask cookbook, the 22000 line format, and the refusal cheat.

- **[`recipes.md`](recipes.md)** — ten copy-paste `run_sequence`
  cookbooks: cold-start recon, PMKID fastpath, 4-way with deauth,
  evil-twin diff, hidden-SSID reveal, WPA3 downgrade, beacon-IE decode,
  probe-request harvest, captive-portal framework, scoring-bot
  fingerprint.

- **[`wctf_playbook.md`](wctf_playbook.md)** — subgenre index over
  [`knowledge/ctf/`](../knowledge/ctf/) (23 files). What each puzzle
  type looks like in the first 60 seconds, which MCP tools to reach
  for, common flag-hiding patterns.

### When things go wrong

- **[`troubleshooting.md`](troubleshooting.md)** — flowcharts per
  failure mode. `capture_handshake` returned ok but no EAPOL; crack
  stuck at 0%; deauth refused; SSH dropped mid-engagement; rogue AP
  won't launch; API 401/429/5xx.

- **[`handshake_forensics.md`](handshake_forensics.md)** — the
  diagnostic between capture and crack. Is my `.22000` valid?
  Recapture, or crack anyway?

### Orientation and rules-of-engagement

- **[`field_notes.md`](field_notes.md)** — venue-agnostic operator
  field notes. Engagement matrix (WCTF / red team / blue team / home
  lab), village survey, DEF CON specifics as one case study among
  many. **Updated yearly at minimum.**

- **[`transport_split.md`](transport_split.md)** — long-form version
  of the "API vs SSH" section in `attic/plan-organize.md`, with
  per-capability reasoning and known cross-firmware drifts.

- **[`legal_and_consent.md`](legal_and_consent.md)** — the
  `--i-own-the-airspace` flag, per-session authorization scopes (SSID
  / MAC allowlists), and the DEFCON-WCTF-vs-office-lab distinction.
