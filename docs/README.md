# docs/

Long-form guides. Distinct from `knowledge/` — `knowledge/` is
zine-flavored, cited, historically-aware corpus material the MCP
serves as resources; `docs/` is operator documentation for humans
using the tool.

Same shape as PHR34CKER5's `docs/`. The tool-orchestration side ships
in `skills/pineapple/SKILL.md`; the guides below are the longer-form
operator material.

## Guides

- **[`pineapple_setup.md`](pineapple_setup.md)** — first-time-through
  walkthrough: unbox, factory reset, laptop USB-tether at
  `172.16.42.1`, admin bootstrap, bearer token retrieval, SSH key
  upload, env-var table, install line, and both-transports smoke test.

- **[`wctf_playbook.md`](wctf_playbook.md)** — the operator-facing WCTF
  playbook. For each puzzle subgenre in `knowledge/ctf/` (23 files:
  hidden-ssid-mazes, pmf-required-targets, wpa2-crack-flags,
  wpa3-transition-downgrade, evil-twin-farms,
  captive-portal-cred-flags, pmkid-fastpath, beacon-flag-stego,
  probe-request-flag, deauth-forensics, rogue-radius-eap-flag,
  wps-pin-flag, ssid-confusion-flag, kr00k-tail-flag, wifi7-mlo-flag,
  wifi6e-6ghz-flag, hotspot2-anqp-flag, ft-handshake-flag,
  framing-frames-flag, cert-phish-eap-flags, default-psk-flags,
  scoring-recon, strategy): what it looks like in the first 60
  seconds, which MCP tools to reach for, common flag-hiding patterns.

- **[`transport_split.md`](transport_split.md)** — long-form version
  of the "API vs SSH" section in `attic/plan-organize.md`, with
  per-capability reasoning and known cross-firmware drifts.

- **[`legal_and_consent.md`](legal_and_consent.md)** — the
  `--i-own-the-airspace` flag, per-session authorization scopes (SSID
  / MAC allowlists), and the DEFCON-WCTF-vs-office-lab distinction.
