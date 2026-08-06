"""
Transport-selection glue: picks API-or-SSH per MCP capability.

Phase 0 stub. Reads `records/pineapple_endpoints.json`, honors any
override in `PINEAPPLE_TRANSPORT_PREF`, and hands each MCP tool a
concrete API or SSH callable to invoke.

The decision rule (from plan-organize.md):

  1. If the WebUI does it and the shape is stable across firmwares
     → API.
  2. If it is raw-radio, needs a subprocess, or touches files → SSH.
  3. If both work, prefer API for observability + rate limiting;
     prefer SSH for low-latency loops (channel hop, packet inject) and
     when we need to `tail -f` a running process.
  4. If a capability only exists on one transport, mark it so and do
     not pretend the other is a fallback.

Emits `{transport: "api"|"ssh"}` into every tool response envelope so
callers can tell which surface answered.
"""

from __future__ import annotations
