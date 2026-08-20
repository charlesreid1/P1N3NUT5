# WPA2 crack flags — "the PSK is the flag"

The classic. Capture the 4-way (or PMKID), crack the PSK, hand over
the PSK.

## Recognition

Beacon carries an RSN IE with AKM 2 (PSK) and no AKM 8. RSN
Capabilities MFPR=0 (or 1 in transition mode). Live clients probing.

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 15},
    {"action": "recon_stop"},
    # PMKID first — client-free.
    {"action": "capture_pmkid",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 45},
    # If PMKID lands, skip the deauth step.
    {"action": "capture_handshake",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "client": "11:22:33:44:55:66",
     "deauth_count": 3,
     "timeout_s": 30},
    {"action": "convert_to_hashcat",
     "mode": 22000,
     "pcap_path": "/tmp/capture.pcapng",
     "out_path": "/tmp/hs.22000"},
    {"action": "crack_start",
     "hash_path": "/tmp/hs.22000",
     "wordlist_path": "/opt/wordlists/rockyou.txt",
     "rules": ["best64.rule"],
     "mode": 22000},
])
```

## The flag surface

Usually the PSK itself — DEFCON WCTF puzzles hand out flags in the
form of the passphrase. Occasionally the puzzle wants you to
*validate* the crack by decrypting a data frame from the pcap:

```
tshark -r capture.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"wpa-pwd\",\"<PSK>:<ESSID>\"" \
  -Y "http.request"
```

The decrypted payload may hold `flag{...}` in a header, body, or DNS
query.

## What if rockyou doesn't crack it?

- **Try `best64.rule`, `d3ad0ne.rule`, `OneRuleToRuleThemAll`.**
- **Try masks.** 8-digit, `?l?l?l?l?d?d?d?d`, `?u?l?l?l?l?d?d?d?d`.
- **SSID-derived.** `cewl` the venue's site + year masks.
- **Vendor-default derivation.** If the SSID matches a default regex,
  see `default-psk-flags.md`.

## When to give up on the fastpath

- **PMF-required + WPA3-SAE only.** Move to `wpa3-transition-downgrade`
  or `dragonblood-deep`.
- **No client, no PMKID, transition mode not present.** Wait, or
  bring one — the Pineapple's second radio can pose as a target
  client (association attempt = M1 = PMKID).

## What still works when PMF-required

The sequence above deauths a client to force a 4-way. When
MFPR=1 on the beacon (or the target is 6 GHz, where PMF is
mandatory), drop the `capture_handshake`+`deauth_count` step
and replace it with PMF-safe capture paths:

- **PMKID capture is unaffected.** M1 with a non-zero PMKID
  field is not PMF-protected — the 4-way isn't robust-mgmt. The
  step 3 `capture_pmkid` line above still runs. This is the
  primary path against PMF-required WPA2/3-transition targets.
- **Natural-reassoc wait.** Skip the deauth, extend the capture
  window (`timeout_s=300`), and let the client roam or
  re-associate on its own. Slower but no attack surface.
- **Bring your own client.** Second Pineapple radio poses as a
  target client; its association attempt to the AP produces an
  M1 PMKID. No deauth needed, no live victim needed.
- **Kr00k tail-frame decrypt (CVE-2019-15126 / -2020-3702).**
  On a vulnerable Broadcom/Cypress/QCA STA, a natural disassoc
  leaks queued frames encrypted under a zero PTK. Some WCTF flag
  payloads sit specifically in that tail.
- **Transition-mode carve-out.** If MFPR=1 but MFPC clients
  coexist with PMF-off clients (transition mode), the PMF-off
  clients are still deauthable. `list_clients` will tag PMF
  state per STA — target them.
- **FT reassoc capture (802.11r).** If the mobility domain is
  in play, FT reassoc frames yield hashcat-22000 material even
  without a deauth.

## Cite

- attacks.json: `wpa2-4way-capture`, `pmkid-capture`,
  `kr00k-broadcom-cve-2019-15126`, `ft-reassoc-capture`.
- Steube 2018; aircrack-ng docs; hashcat wiki.
- IEEE Std 802.11-2020 §11.34 (PMF), §12.7.6 (4-way handshake).
