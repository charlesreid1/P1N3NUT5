# hostapd-wpe — Wireless Pwnage Edition

**Verified against:** hostapd-wpe (patch against hostapd 2.10) as of 2026-Q3

A patch series on top of hostapd that adds **inner-EAP logging**:
MSCHAPv2 challenge/response captured, EAP-GTC plaintext captured,
PEAP inner-method downgrade knobs, cert phishing hooks.

## What WPE adds

- **Inner-method downgrade behavior** — the WPE variant of hostapd
  accepts inner-method downgrade offers from clients even when they
  requested a stronger inner method. Clients with weak cert
  validation get pushed onto MSCHAPv2 (or worse, GTC). (eaphammer
  exposes this as `--negotiate weakest`; hostapd-wpe's config-file
  `eap_user` list drives the equivalent behavior.)
- **Challenge/response logging** — every captured MSCHAPv2 exchange
  is written to `/var/log/hostapd-wpe.log` in a format that both
  `asleap` and `hashcat -m 5500` accept as input.
- **Cert bundle** — WPE ships a default self-signed CA / server-cert
  pair; regenerate for your engagement.

## Config diff vs stock hostapd

```
ieee8021x=1
eap_server=1
eap_user_file=/etc/hostapd-wpe/hostapd-wpe.eap_user
ca_cert=/etc/hostapd-wpe/certs/ca.pem
server_cert=/etc/hostapd-wpe/certs/server.pem
private_key=/etc/hostapd-wpe/certs/server.key
private_key_passwd=whatever
dh_file=/etc/hostapd-wpe/certs/dh
```

`hostapd-wpe.eap_user` accepts every user + any inner method by
default — the point is to log what the client sends.

## Log format for hashcat

```
$ tail -f /var/log/hostapd-wpe.log
username:      alice
challenge:     5e9d...                      # 8-byte ChallengeHash
response:      a782...                      # 24-byte NTResponse
jtr NETNTLM:   alice:$NETNTLM$5e9d...$a782...
hashcat 5500:  alice::::a782...:5e9d...     # user::domain::<NTResp>:<ChallengeHash>
```

The `hashcat 5500` line goes straight into a file that
`hashcat -m 5500 hashfile rockyou.txt` cracks. `challenge` is the
pre-derived 8-byte `ChallengeHash`, not the raw 16-byte
`PeerChallenge` — see the shared derivation callout in
`enterprise/reference.md`.

## When to reach for WPE vs eaphammer

- **WPE** — you already run hostapd, want minimal delta, know your
  target's client behavior.
- **eaphammer** — you want cert templating, portal hosting, and
  multiple attack profiles ready to go.

## Cite

- hostapd-wpe GitHub (OpenSecurityResearch).
- attacks.json: `rogue-radius-hostapd-wpe`.
