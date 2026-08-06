"""
P1N3NUT5 MCP server — tool declarations.

Phase 0 stub. Will host the FastMCP app and register every tool listed
under "MCP tool inventory" in plan-organize.md:

  Know    — list_topics, read_lore, search_lore, random_lore,
            lookup_standard, lookup_channel, lookup_frame, lookup_ie,
            lookup_cipher, lookup_eap, lookup_attack, lookup_cve,
            lookup_hashcat_mode, verify_claim, explain_attack,
            bibliography, cross_reference, search_records
  Act     — pineapple_status, list_interfaces, recon_*, list_aps,
            list_clients, list_probe_requests, list_associations,
            client_history, get_ap_details, recon_download,
            pineap_*, filter_*, create_rogue_ap, evil_twin,
            serve_captive_portal, rogue_radius, deauth,
            capture_handshake, capture_pmkid, beacon_flood,
            probe_flood, packet_inject, channel_hop_*,
            client_disassoc
  Perceive— parse_pcap, extract_handshakes, extract_pmkids,
            convert_to_hashcat, crack_start, crack_status,
            crack_result, crack_stop, decode_ies, beacon_diff,
            client_fingerprint
  Orchestrate — run_sequence, call_log

Every tool that touches the Pineapple returns the stable envelope
    {ok, transport, payload, timing_ms, warnings[]}
declared in plan-organize.md.
"""

from __future__ import annotations
