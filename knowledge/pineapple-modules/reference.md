# Pineapple modules (Mark VII) — reference

The Mark VII firmware ships a first-party module system: PineAP,
Recon, Filters, Reporting. Beyond those, Hak5 hosts a community module
repository, and modules can also be side-loaded from `.tar.gz` archives
built out-of-band. This file catalogs the module surface P1N3NUT5
either drives directly (over the REST API) or shells out to (over SSH
when a module ships CLI helpers). PineAP itself is documented in
`pineap/` — this topic is everything *else* under `/api/modules/*`.

## Where modules live on disk

- `/pineapple/modules/<slug>/` — one directory per installed module.
  - `module.info` — JSON metadata (name, version, author, permissions).
  - `api/module.php` (legacy) or a Python `api.py` (Mk VII) — backing
    handlers for the module's WebUI.
  - `js/`, `css/`, `assets/` — front-end assets.
  - `bootstrap.sh` — optional first-run hook (chmod binaries, copy
    configs into `/etc/`, register a `procd` service).
  - `bin/` — module-shipped binaries (e.g. `hostapd-mana`,
    `hcxdumptool` variants) if the module ships its own.
- Logs land under `/pineapple/modules/<slug>/log/` or `/tmp/<slug>.log`
  depending on the module's conventions.

Any module can be enumerated via SSH with `ls /pineapple/modules/`;
the API surface (`GET /api/modules`) is the same list plus install
metadata.

## The module lifecycle

Same shape regardless of first- or third-party origin:

| stage | REST | SSH equivalent |
| ----- | ---- | -------------- |
| discover | `GET /api/modules/available` | (community index over HTTPS) |
| install  | `POST /api/modules/install {slug}` | `opkg install <slug>` if opkg-packaged; otherwise scp the tarball and unpack |
| enable   | `POST /api/modules/enable {slug}` | touch `/pineapple/modules/<slug>/enabled` |
| status   | `GET /api/modules/<slug>` | `cat /pineapple/modules/<slug>/module.info` |
| disable  | `POST /api/modules/disable {slug}` | rm the `enabled` marker |
| uninstall | `POST /api/modules/uninstall {slug}` | `rm -rf /pineapple/modules/<slug>/` (destructive) |

The API records for these paths are `pep-list-modules`,
`pep-install-module`, `pep-uninstall-module` in
`pineapple_endpoints.json`. Enable/disable/status are variants that
share `auth_scope: modules.write`.

## First-party module surface

- **PineAP** — see `pineap/reference.md`. Config, filters, probe log.
- **Recon** — the WebUI's scan engine. AP + client + probe DB.
  Backing endpoints under `/api/recon/*` (see `pep-list-aps`,
  `pep-list-clients`, `pep-list-probes`).
- **Filters** — SSID and MAC allow/deny lists shared across PineAP,
  Recon, and the WebUI's alerting. Endpoints `pep-filter-ssid-*`,
  `pep-filter-client-*`.
- **Dashboard** — status page. `GET /api/dashboard`.
- **Reporting** — email/webhook alerts on filter hits and PineAP events.
  Rarely useful mid-CTF but the config is worth knowing so an assistant
  doesn't accidentally trip a webhook alert during recon.

## Third-party / community modules P1N3NUT5 reaches for

Names below are the canonical community slugs as of firmware 3.x.
Availability drifts across firmware revisions; the assistant should
`list_modules()` first before assuming a slug exists.

- **evil-portal** — captive portal generator. Ships DHCP + dnsmasq +
  nginx + a template library. Templates render vendor login pages
  (Starbucks, Xfinity, Google, generic corp). The `serve_captive_portal`
  MCP tool wraps evil-portal when it is installed and falls back to a
  hand-rolled nginx + hostapd stack when it is not.
- **key-manager** — SSH key management on the Pineapple side; useful
  for scripted engagements that provision the device fresh.
- **site-survey** — periodic RSSI walk-around, exports CSV. Useful for
  antenna aiming and channel-selection decisions before the CTF starts.
- **recon-analyzer** — post-processing on the recon DB. Aggregates by
  vendor OUI, sorts by client count, flags high-value APs.
- **eaphammer-wrapper** — some firmware revisions bundle a wrapper for
  Gabriel Ryan's eaphammer. See `eaphammer/` for the tool itself;
  the wrapper simplifies profile install but the SSH driver in
  `attacks.py` calls `eaphammer` directly for reproducibility.
- **dwall** (legacy) — traffic display for associated clients. Rarely
  useful under modern encryption; kept in the ecosystem for
  captive-portal + open-SSID contexts.
- **hostapd-mana wrapper** — some Mk VII community bundles ship a
  wrapper module for SensePost's hostapd-mana (see `karma-family/`).
  The MCP prefers driving hostapd-mana directly over SSH because the
  wrapper's module.info version has lagged the upstream project.

## Sideloading a module

When a community module isn't in the built-in repo:

1. Build or download the `.tar.gz` on the laptop.
2. `scp <slug>.tar.gz root@172.16.42.1:/tmp/`
3. `ssh root@172.16.42.1 'cd /pineapple/modules && tar -xzf /tmp/<slug>.tar.gz'`
4. Run `bootstrap.sh` if present.
5. Restart the module manager: `/etc/init.d/pineapd restart` — the
   WebUI now sees the module in `list_modules()`.

The MCP's `install_module` tool prefers the API path; sideload is an
SSH fallback and is annotated as such in `pineapple_endpoints.json`.

## Permissions and `auth_scope`

Every API path a module exposes registers an `auth_scope`. For the
first-party set:

- `modules.read` — list, status
- `modules.write` — install, enable, disable, uninstall
- `pineap.read` / `pineap.write`
- `recon.read` / `recon.write`

A module's own paths inherit the module's declared scope. Third-party
modules are expected to declare scope but historically some ship as
`modules.write` catch-all — worth checking `module.info` when
scripting.

## Logs and troubleshooting

- `logread -f` (SSH) — the OpenWRT unified log; every module writes here.
- `/pineapple/modules/<slug>/log/` — module-scoped logs.
- `/tmp/<slug>.log` — some modules land here instead.
- `procd` supervises long-running module services; `service <slug>
  status` when a module ships one.

Common failure modes:

- **Module installs but doesn't appear in WebUI.** `module.info` JSON
  is malformed. `ssh root@... 'jq . /pineapple/modules/<slug>/module.info'`
  will surface the parse error.
- **Module fails to start after firmware upgrade.** `bootstrap.sh` may
  need to re-run, or a bundled binary was compiled against an older
  libc. Reinstall from the repo is the fast path.
- **API endpoint 401s.** Token lacks the module's declared scope.
  Re-issue the token from the WebUI Admin page with the scope checked.

## Interaction with the MCP tool surface

P1N3NUT5 exposes:

- `list_modules()` — thin wrapper over `pep-list-modules`.
- `install_module(slug)` / `uninstall_module(slug)` — API-only for
  determinism; SSH sideload is `sideload_module(path)`.
- `enable_module(slug)` / `disable_module(slug)`.
- Higher-level tools (`serve_captive_portal`, `create_rogue_ap`) check
  for the relevant module and fall back to hand-rolled SSH if absent.

The intent: the assistant asks "is evil-portal here?" via
`list_modules`, and if yes uses the module's built-in template
selection; if no, the MCP builds the same captive portal from
first principles over SSH.

## Cite

- Hak5 WiFi Pineapple Mark VII documentation (module system, REST paths).
- `knowledge/records/pineapple_endpoints.json` — record catalog for
  every `/api/modules/*` path.
- `knowledge/pineap/reference.md` — the first-party PineAP module.
- `knowledge/karma-family/reference.md` — hostapd-mana context.
- `knowledge/eaphammer/reference.md` — the tool the wrapper module wraps.
