# transport_split — API vs SSH

Every Pineapple-touching MCP tool returns
`{ok, transport, payload, timing_ms, warnings[]}`. The `transport`
key is not decoration: it names which surface actually answered, and
different surfaces have different failure modes. Callers who blindly
retry an API-only tool on SSH end up waiting for a connection they
can't establish.

## The rule

From
[`pineapple_transport.py:CAPABILITY_RULES`](../src/p1n3nut5_mcp/pineapple_transport.py):

1. **If the WebUI does it and the shape is stable across firmwares →
   API.** Recon start/stop, PineAP config, filter management — the
   dashboard's own endpoints. Rate-limited, but structured.
2. **If it is raw-radio, needs a subprocess, or touches files → SSH.**
   deauth, capture, injection, hostapd for rogue APs, hcxdumptool for
   PMKID, pcap upload/download, `iw dev` incantations.
3. **If both work, prefer API for observability + rate limiting;
   prefer SSH for low-latency loops and when we need to `tail -f` a
   running process.**
4. **If a capability only exists on one transport, mark it so and do
   not pretend the other is a fallback.**

`PINEAPPLE_TRANSPORT_PREF=api|ssh` overrides the default rule for the
whole session — useful when the API is rate-limited mid-engagement,
or when SSH is blocked by venue firewall.

## Capability table

Every entry in `CAPABILITY_RULES` and its preferred/fallback surface.
Sourced from the actual dict; keep in sync when new capabilities land
(coverage tests will catch drift — `tests/test_coverage_matrix.py`).

| capability            | preferred | fallback |
|-----------------------|-----------|----------|
| `status`              | api       | ssh      |
| `list_aps`            | api       | ssh      |
| `list_interfaces`     | ssh       | —        |
| `list_associations`   | api       | —        |
| `recon_start`         | api       | —        |
| `recon_stop`          | api       | —        |
| `recon_status`        | api       | —        |
| `list_clients`        | api       | —        |
| `list_probe_requests` | api       | —        |
| `pineap_status`       | api       | —        |
| `pineap_start`        | api       | —        |
| `pineap_stop`         | api       | —        |
| `pineap_config`       | api       | —        |
| `pineap_beacon_add`   | api       | —        |
| `pineap_beacon_remove`| api       | —        |
| `get_ap_details`      | api       | —        |
| `filter_ssid_list`    | api       | —        |
| `filter_client_list`  | api       | —        |
| `deauth`              | ssh       | —        |
| `capture_handshake`   | ssh       | —        |
| `capture_pmkid`       | ssh       | —        |
| `create_rogue_ap`     | ssh       | —        |
| `stop_rogue_ap`       | ssh       | —        |
| `stop_all_rogue_aps`  | ssh       | —        |
| `list_rogue_aps`      | ssh       | —        |
| `enforce_rogue_limits`| ssh       | —        |
| `beacon_flood`        | ssh       | —        |
| `packet_inject`       | ssh       | —        |
| `channel_hop_start`   | ssh       | —        |
| `channel_hop_stop`    | ssh       | —        |

The perception tools (`parse_pcap`, `extract_handshakes`,
`extract_pmkids`, `convert_to_hashcat`, `decode_ies`, `beacon_diff`,
`client_fingerprint`, hashcat control) run **locally** on the MCP
host — no Pineapple transport involved. They're not in
`CAPABILITY_RULES` and don't return a `transport` key.

## Cross-firmware drifts

Every endpoint in `knowledge/records/pineapple_endpoints.json` carries
`firmware_min` (100% coverage per `test_depth.py`). The pinned floor
is `3.0.0` for the whole surface; the 3.0 → 3.1 delta is a payload
*shape* change, not an endpoint move:

- **`list_aps` / `list_clients`.** 3.0 returns a flat `security`
  string ("wpa2", "wpa3", "open"). 3.1 nests it:
  `{"akm": 2, "cipher": "ccmp", "pmf": "capable"}`. `recon.py`
  normalizes both to the canonical `{security, security_detail}`
  shape declared in
  `records/pineapple_endpoints.json:pep-list-aps.api.response_shape`.
- **`recon/probes`.** 3.0 keyed on `lastSeen`; 3.1 on `last_seen`.
  Same normalizer path.
- **`pineap/config`.** 3.1 added `karma_pool_ssid_max`; setting it on
  3.0 is a no-op with a warning.

When a shape drift is severe enough to break the normalizer, the
record's `disputed` field surfaces both values and `verify_claim`
returns `needs_qualification`. See the `hak5-mk7-docs` bib entry for
the version-gated source of truth.

## Env override

```
export PINEAPPLE_TRANSPORT_PREF=api   # force API where both work
export PINEAPPLE_TRANSPORT_PREF=ssh   # force SSH where both work
unset PINEAPPLE_TRANSPORT_PREF        # let CAPABILITY_RULES decide
```

When the requested transport isn't supported for a given capability,
`choose()` in `pineapple_transport.py` raises `ValueError` at the
tool boundary. This is *not* a warning — a mismatch means the caller
has misread the split. Fix the request, don't retry.

## When to reach for which

- **API rate-limited mid-recon.** Set `PINEAPPLE_TRANSPORT_PREF=ssh`
  for the session; `list_aps` falls back to `iw dev wlanX scan`
  parsing.
- **SSH blocked by venue firewall.** Set `PINEAPPLE_TRANSPORT_PREF=api`
  and stick to recon + PineAP for the engagement; transmitting tools
  will refuse because they're SSH-only.
- **Long deauth loop, low latency needed.** Prefer SSH — one
  connection, many `run()` calls, `call_log` captures every
  invocation.
- **Post-engagement audit.** `orchestrate.call_log()` merges the SSH
  and API call logs into one timeline (L5). Do the audit off the
  merged log, not off either transport alone.
