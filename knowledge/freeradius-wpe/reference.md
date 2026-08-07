# freeradius-wpe — reference

`freeradius-wpe` is the freeradius counterpart to `hostapd-wpe`.
Where `hostapd-wpe` patches hostapd to log inner-EAP material,
`freeradius-wpe` patches freeradius to do the same at the RADIUS
level. Useful when you want a *real* RADIUS on the back end (with
freeradius's inner-EAP flexibility) rather than the mini-RADIUS
embedded in hostapd.

Read alongside `enterprise/`, `hostapd-wpe/`, `eaphammer/`.

## When you'd use freeradius-wpe instead of hostapd-wpe

- **You want to inspect inner-EAP flows beyond MSCHAPv2** —
  freeradius supports EAP-PWD, EAP-FAST, EAP-TLS 1.3, EAP-IKEv2.
- **You want a fake-realm forwarder** — freeradius can pretend to
  forward auth to another RADIUS while logging locally.
- **You want to test complex Passpoint / HS2.0 flows** — freeradius
  has richer plugin support than hostapd's built-in.
- **You have multiple hostapd instances (multi-radio Pineapple)
  pointing at one RADIUS** — a shared freeradius-wpe on the loopback
  is cleaner than two hostapd-wpe processes.

## Config diff vs stock freeradius

The WPE patch adds instrumented modules:

- **`raddb/mods-available/eap_wpe`** — logs each inner-method
  challenge/response as it happens.
- **`raddb/sites-available/wpe`** — an "outer" site that accepts
  from hostapd, invokes the WPE inner-EAP module, and never rejects.
- **Log file at `/var/log/freeradius-wpe.log`** — hashcat-formatted
  MSCHAPv2, plaintext GTC tokens, EAP-TTLS-PAP passwords.

Stock freeradius already logs auth events; WPE's addition is that
it logs the *cryptographic material* usable for offline crack,
extracted from the EAP tunnel, in a format hashcat / asleap can
consume directly.

## Interoperation with hostapd

`hostapd.conf` on the Pineapple:

```
wpa=2
wpa_key_mgmt=WPA-EAP
ieee8021x=1
auth_server_addr=127.0.0.1
auth_server_port=1812
auth_server_shared_secret=testing123
```

freeradius-wpe listens on 1812 with the matching secret. Every
Access-Request from hostapd triggers the WPE-instrumented EAP flow.

## Log format

Example log line (MSCHAPv2 capture):

```
Sun Aug  4 21:14:03 2026
    username:  alice@corp.local
    challenge: e3ac2d1f6b8c4092
    response:  8e2f...  # 24 bytes hex
    hashcat -m 5500:  alice::corp:8e2f...:e3ac2d1f6b8c4092
    john NETNTLM:     alice:$NETNTLM$e3ac2d1f6b8c4092$8e2f...
```

Plaintext GTC:

```
Sun Aug  4 21:15:07 2026
    username: bob
    gtc_token: 918273-Duo   # the flag surface for GTC-flag puzzles
```

## Cite

- freeradius-wpe fork (frontline-radius / brad-anton / joswr1ght).
- freeradius upstream documentation (freeradius.org).
- RFC 2759 — MSCHAPv2.
- attacks.json: `rogue-radius-hostapd-wpe`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-gtc-plaintext-token-capture`.
