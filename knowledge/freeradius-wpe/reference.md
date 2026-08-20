# freeradius-wpe — reference

**Verified against:** brad-anton/freeradius-wpe (patch series against FreeRADIUS 3.0.x) as of 2026-Q3

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

The WPE patch is applied against the *existing* freeradius tree,
not a parallel `wpe` site/module. Where things live after `make
install` on a Debian/Ubuntu freeradius layout:

- **`/etc/freeradius/3.0/sites-available/default`** — the stock
  "default" virtual server, patched to log inner-EAP material and
  never reject during phase-2.
- **`/etc/freeradius/3.0/mods-available/eap`** — the stock EAP
  module, patched with the WPE instrumentation for MSCHAPv2 / GTC
  / PAP.
- **`/var/log/freeradius/radius.log`** — the auth-log path used by
  packaged freeradius. WPE writes each captured challenge/response
  and plaintext GTC token here in a hashcat/asleap-friendly format.
- **`/etc/freeradius/3.0/mods-config/files/authorize`** — the
  credentials file WPE writes captured usernames + hashcat lines to
  as they land (mirrors the log for easier consumption).

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
    username:      alice@corp.local
    challenge:     e3ac2d1f6b8c4092              # 8-byte ChallengeHash
    response:      8e2f...                       # 24-byte NTResponse
    hashcat -m 5500: alice::corp::8e2f...:e3ac2d1f6b8c4092
    john NETNTLM:    alice:$NETNTLM$e3ac2d1f6b8c4092$8e2f...
```

The 8-byte `challenge` above is the SHA1-derived MSCHAPv2
`ChallengeHash`, not the raw 16-byte PeerChallenge. WPE pre-derives
it for you — see the shared "ChallengeHash derivation" callout in
`enterprise/reference.md` for the formula. The hashcat 5500 line
uses four `::`-separated fields:
`user::domain::<NTResponse>:<ChallengeHash>`.

Plaintext GTC:

```
Sun Aug  4 21:15:07 2026
    username: bob
    gtc_token: 918273-Duo   # the flag surface for GTC-flag puzzles
```

## Cite

- freeradius-wpe canonical fork: **brad-anton/freeradius-wpe** on
  GitHub (patches against FreeRADIUS 3.0.x).
- freeradius upstream documentation (freeradius.org).
- RFC 2759 — MSCHAPv2.
- attacks.json: `rogue-radius-hostapd-wpe`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-gtc-plaintext-token-capture`.
