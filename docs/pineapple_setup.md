# pineapple_setup — first-time-through

Get the Hak5 WiFi Pineapple Mark VII on your bench, get the MCP
talking to it on both transports, run a smoke test. If any step
fails, `pineapple_status()` is the diagnostic first stop.

## Prereqs

- **Pineapple Mark VII** with recent firmware (`3.x`). Ships from Hak5
  on `172.16.42.1` when USB-tethered to a laptop.
- **Laptop with USB-C tether** — the MCP treats the Pineapple as a
  network peer, not as a host-attached USB device. On macOS/Linux,
  plug the Pineapple in and the tether interface comes up on
  `172.16.42.0/24` with the Pineapple on `.1` and your laptop on
  `.42` or `.43`.
- **Admin bootstrap** — first boot needs the WebUI wizard. Visit
  `https://172.16.42.1:1471`, accept the self-signed cert, set an
  admin password. This is the account the API bearer token belongs
  to.
- **Bearer token** — WebUI → Configuration → API. Copy the token.
  You'll set it as `PINEAPPLE_TOKEN`. Rotate this if you share the
  device with someone.
- **SSH key** — WebUI → Configuration → SSH → paste your public key
  into `authorized_keys`. The MCP prefers key auth over password
  auth. If you must use a password, set `PINEAPPLE_SSH_PASSWORD`
  instead of `PINEAPPLE_SSH_KEY`.

## Env vars

Every variable `runtime.py:Config.from_env` reads. Set what you need
in your shell env (`.envrc`, `direnv`, systemd unit — whatever
matches your setup):

| var | controls | default | when to set |
|-----|----------|---------|-------------|
| `PINEAPPLE_HOST` | Pineapple IP / hostname | — (required) | always |
| `PINEAPPLE_TOKEN` | API bearer token | — | any API-transport tool |
| `PINEAPPLE_SSH_USER` | SSH username | `root` | non-root user (rare) |
| `PINEAPPLE_SSH_KEY` | path to SSH private key | — | key auth (preferred) |
| `PINEAPPLE_SSH_PASSWORD` | SSH password | — | password auth (fallback) |
| `PINEAPPLE_SSH_PORT` | SSH port | `22` | non-default port |
| `PINEAPPLE_TRANSPORT_PREF` | force `api` or `ssh` when both work | unset | API rate-limited, or SSH blocked |
| `MAX_ROGUE_MINUTES` | rogue-AP wall-clock cap | `0` (unlimited) | office lab / long engagement |
| `P1N3NUT5_KNOWLEDGE` | knowledge/ dir override | packaged copy | dev against a live checkout |
| `HASHCAT_PATH` | hashcat binary path | `hashcat` on PATH | non-default install |
| `WORDLIST_DIR` | wordlist root for `crack_start` | — | resolve relative wordlists |

`MAX_ROGUE_MINUTES=0` means unlimited (L4 semantics). Any positive
value is a hard cap: `enforce_rogue_ap_limits` kills every rogue AP
older than N minutes.

## Install

```
pip install .
```

The single install line covers everything: MCP server, transports,
pcap parsing (both classic pcap and pcapng — scapy is a hard
dependency), record loader, hashcat integration. The `dev` extra
adds pytest + pytest-asyncio for the test suite:

```
pip install .[dev]
```

The `[pcap]` extra was removed in Phase L6 — scapy moved from
optional to required so `parse_pcap` handles pcapng out of the box.

## Smoke test

Both transports should answer. From a Python shell:

```python
import asyncio
from p1n3nut5_mcp.server import pineapple_status

# API path
print(asyncio.run(pineapple_status(transport="api")))
# → {"ok": True, "transport": "api", "payload": {...firmware/uptime/radios...}, "timing_ms": N, "warnings": []}

# SSH path
print(asyncio.run(pineapple_status(transport="ssh")))
# → {"ok": True, "transport": "ssh", "payload": {...}, "timing_ms": N, "warnings": []}
```

If the API path returns `PermissionError` — check `PINEAPPLE_TOKEN`.
If the SSH path returns `MissingConfig` — you need either
`PINEAPPLE_SSH_KEY` or `PINEAPPLE_SSH_PASSWORD`. `Config.from_env`
also warns at process start if neither is set, so an SSH-first
engagement fails visibly instead of at the first `do_deauth`.

## MCP integration

The server is registered as the `p1n3nut5-mcp` entry point. From a
client that speaks MCP (Claude Desktop, Continue, etc.), point it at
`p1n3nut5-mcp` with the env above; the client picks up every tool
under `server.py:main()`.

## Troubleshooting

- **`pineapple_status()` returns ok=True but no radios** — check
  `iw dev` over SSH. `wlan0` and `wlan1` should both be present.
- **API returns HTTP 401** — token expired or rotated. Regenerate.
- **SSH returns `Connection refused`** — SSH is off. Turn it on in
  the WebUI (Configuration → SSH).
- **`enforce_rogue_ap_limits` doesn't kill anything** —
  `MAX_ROGUE_MINUTES=0` means unlimited by design. Set a positive
  value if you want the cap to fire.
