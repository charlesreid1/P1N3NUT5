"""
Typed record loader for `knowledge/records/*.json`.

Phase 0 stub. Mirrors PHR34CKER5's records module. Will hold:

  * a schema-validated loader for every record type declared in
    plan-knowledge.md (standards, channels, frame_types, ies,
    security_suites, eap_methods, attacks, cves, hashcat_modes,
    pineapple_endpoints, openwrt_uci, defense_and_detection,
    bibliography)
  * a citation-integrity check — every `citations[]` entry must resolve
    to a `bibliography.json` id; loader raises on violation
  * lookup helpers backing the `lookup_*` and `search_records` MCP
    tools, each returning the envelope
        {citations[], era_bounds, region, confidence}
"""

from __future__ import annotations
