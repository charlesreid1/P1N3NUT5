"""
Transport-selection glue: picks API-or-SSH per MCP capability.

Phase 1 sets the shape. `pineapple_status()` is the first capability
that works on both surfaces, so it's the honest test of the rule:

  1. If the WebUI does it and shape is stable across firmwares → API.
  2. If it is raw-radio, needs a subprocess, or touches files → SSH.
  3. If both work, prefer API for observability + rate limiting; prefer
     SSH for low-latency loops and when we need to `tail -f` a running
     process.
  4. If a capability only exists on one transport, mark it so and do
     not pretend the other is a fallback.

`PINEAPPLE_TRANSPORT_PREF=api|ssh` overrides the default rule for the
whole session — useful when the API is rate-limited mid-engagement, or
when SSH is blocked by venue firewall.
"""

from __future__ import annotations

from typing import Literal

from p1n3nut5_mcp.runtime import Config, Transport

# Capability → (preferred, fallback|None). Phase 1 seeds this from the
# rules in plan-organize.md. Phase 2 will move this into
# records/pineapple_endpoints.json so it's dated + firmware-pinned.
CAPABILITY_RULES: dict[str, tuple[Transport, Transport | None]] = {
    "status": ("api", "ssh"),
    "list_aps": ("api", "ssh"),
    "list_interfaces": ("ssh", None),
    "recon_start": ("api", None),
    "recon_stop": ("api", None),
    "recon_status": ("api", None),
    "list_clients": ("api", None),
    "list_probe_requests": ("api", None),
    "list_associations": ("api", None),
    "pineap_status": ("api", None),
    "pineap_start": ("api", None),
    "pineap_stop": ("api", None),
    "pineap_config": ("api", None),
    "pineap_beacon_add": ("api", None),
    "pineap_beacon_remove": ("api", None),
    "get_ap_details": ("api", None),
    "filter_ssid_list": ("api", None),
    "filter_client_list": ("api", None),
    "deauth": ("ssh", None),
    "capture_handshake": ("ssh", None),
    "capture_pmkid": ("ssh", None),
    "create_rogue_ap": ("ssh", None),
    "beacon_flood": ("ssh", None),
    "packet_inject": ("ssh", None),
    "channel_hop_start": ("ssh", None),
    "channel_hop_stop": ("ssh", None),
}


class UnknownCapability(KeyError):
    """Raised when a caller asks for a capability not in the rules table."""


def choose(
    capability: str,
    config: Config,
    request: Literal["api", "ssh"] | None = None,
) -> Transport:
    """Return the transport to use for `capability`.

    Order of precedence:
      1. explicit `request=` argument (caller override)
      2. `PINEAPPLE_TRANSPORT_PREF` env, if the capability supports it
      3. rule from `CAPABILITY_RULES`
    """
    if capability not in CAPABILITY_RULES:
        raise UnknownCapability(capability)
    preferred, fallback = CAPABILITY_RULES[capability]
    supported = {preferred} | ({fallback} if fallback else set())

    if request is not None:
        if request not in supported:
            raise ValueError(
                f"capability {capability!r} does not support transport {request!r}; "
                f"supported: {sorted(supported)}"
            )
        return request

    if config.transport_pref in supported:
        return config.transport_pref  # type: ignore[return-value]

    return preferred
