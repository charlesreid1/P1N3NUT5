"""
Config, credential resolution, and session state.

Phase 0 stub. Owns the lazy-initialized singletons the transport
modules need. Nothing here runs at import time — boot only when the
first Pineapple-flavored MCP tool is invoked, so the offline knowledge
tools stay usable even when `PINEAPPLE_HOST` is not set.

Reads (see the env-var table in plan-organize.md):

  * `PINEAPPLE_HOST` (required for any Act tool)
  * `PINEAPPLE_TOKEN` (required for API transport)
  * `PINEAPPLE_SSH_USER` / `PINEAPPLE_SSH_KEY` / `PINEAPPLE_SSH_PASSWORD`
    / `PINEAPPLE_SSH_PORT` (required for SSH transport)
  * `PINEAPPLE_TRANSPORT_PREF` — override the default per-capability rule
  * `MAX_ROGUE_MINUTES` — auto-teardown safety guardrail
  * `P1N3NUT5_KNOWLEDGE` — dev-mode corpus path override
  * `HASHCAT_PATH` / `WORDLIST_DIR` — crack-tool config

Also owns the per-session `call_log`: every API + SSH command with
timing, transport used, and warnings — exposed via the `call_log`
tool and the `p1n3nut5://sessions/<id>/events` resource.
"""

from __future__ import annotations
