"""
REST client for the Hak5 Pineapple Mark VII WebUI backend.

Phase 0 stub. Will hold:

  * bearer-token auth against `https://<pineapple>/api/…`
  * per-endpoint auth-scope enforcement (recon.read, pineap.write, …)
  * firmware-version detection and per-endpoint firmware_min/max checks
  * structured error surfacing so warnings[] in the tool envelope is
    populated when the WebUI returns a non-2xx or a payload shape drifts
    from the version pinned in `records/pineapple_endpoints.json`

Best for capabilities where the WebUI is authoritative: dashboard,
recon control + data pull, PineAP config, module management, filter
management. See "The transport split — API vs SSH" in plan-organize.md.
"""

from __future__ import annotations
