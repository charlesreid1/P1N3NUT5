# scripts/

Human-run shell + Python helpers. Distinct from `src/` — `src/` is
what runs every time the MCP answers a tool call; `scripts/` is what
you run once, at setup.

Phase 0 has authored none of the scripts below. Same shape as
PHR34CKER5's `scripts/`.

## Planned

- **`setup-pineapple.sh`** — first-time Mark VII setup helper.
  Prompts for `PINEAPPLE_HOST` / bearer token, uploads an SSH public
  key to `/root/.ssh/authorized_keys`, verifies both transports with a
  `pineapple_status()` round-trip, and drops a `pineapple.env` for
  the operator's shell (gitignored). Idempotent.

- **`fetch-firmware-manifest.py`** — one-shot: connect to the
  Pineapple, record its firmware version + module list + module
  versions, and emit a fingerprint used by `records.py` to select the
  right `pineapple_endpoints.json` entries (per-record
  `firmware_min` / `firmware_max`).

- **`generate-pcap-fixtures.py`** — deterministic pcap generator for
  `tests/fixtures/`. Every `frame_types.json` record and every Tier-1
  `attacks.json` record gets a small named fixture so the perception
  tools have a deterministic parse target. Analog of
  PHR34CKER5's `generate-tone-fixtures.py`.

- **`ingest-wordlist.sh`** — copy a wordlist into `WORDLIST_DIR` with
  a size + sha256 report; used before `crack_start`.
