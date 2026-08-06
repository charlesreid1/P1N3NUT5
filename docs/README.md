# docs/

Long-form guides. Distinct from `knowledge/` — `knowledge/` is
zine-flavored, cited, historically-aware corpus material the MCP
serves as resources; `docs/` is operator documentation for humans
using the tool.

Same shape as PHR34CKER5's `docs/`. The `wctf_playbook.md` and
`transport_split.md` bodies are deferred to Phase 2 (they cross-
reference the corpus files that Phase 2 will author); the
tool-orchestration side already ships in `skills/pineapple/SKILL.md`.

## Planned

- **`pineapple_setup.md`** — first-time-through walkthrough:
  unbox, factory reset, laptop USB-tether at `172.16.42.1`, admin
  bootstrap, bearer token retrieval, SSH key upload, and both-
  transports smoke test. Complements `scripts/setup-pineapple.sh`.

- **`wctf_playbook.md`** — the operator-facing WCTF playbook. For
  each puzzle subgenre in Tier 5 of plan-knowledge.md
  (hidden-ssid-mazes, pmf-required-targets, wpa2-crack-flags,
  wpa3-transition-downgrade, evil-twin-farms,
  captive-portal-cred-flags, pmkid-fastpath, beacon-flag-stego,
  probe-request-flag, deauth-forensics, rogue-radius-eap-flag,
  wps-pin-flag): what it looks like in the first 60 seconds, which
  MCP tools to reach for, common flag-hiding patterns.

- **`transport_split.md`** — long-form version of the
  "API vs SSH" section in plan-organize.md, with per-endpoint
  reasoning and known cross-firmware drifts.

- **`legal_and_consent.md`** — the `--i-own-the-airspace` flag,
  per-session authorization scopes (SSID / MAC / time / geo
  allowlists), and the DEFCON-WCTF-vs-office-lab distinction.
