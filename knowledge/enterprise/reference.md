# enterprise — reference

**Verified against:** hostapd 2.10 / freeradius 3.0.x / hashcat 6.2.x as of 2026-Q3

## The chain

```
STA          802.11               AP (Authenticator)         RADIUS (EAP)
 │  auth/assoc                    │                          │
 ├──────────────────────────────►│                          │
 │  EAPOL-Start                   │                          │
 ├──────────────────────────────►│                          │
 │                                │  Access-Request(EAP-Identity)
 │                                ├─────────────────────────►│
 │                                │  Access-Challenge(EAP-Request)
 │                                │◄─────────────────────────┤
 │  EAP-Request                   │                          │
 │◄──────────────────────────────┤                          │
 │  EAP-Response                  │                          │
 ├──────────────────────────────►│                          │
 │                                │  … EAP tunnel established …
 │                                │  MSK derived on both ends
 │  EAPOL-Key M1..M4 (4-way)      │                          │
 ◄──── PTK from MSK derivation ──►                          │
```

The AP never sees the inner method. It ferries EAP frames between
the STA and the RADIUS. The MSK output of the successful EAP
session is what seeds the WPA 4-way handshake.

## AKM selectors

- **`00-0F-AC:01`** — 802.1X + PBKDF2 (legacy).
- **`00-0F-AC:03`** — FT-802.1X (802.11r + Enterprise).
- **`00-0F-AC:05`** — 802.1X + SHA-256 (WPA2 revised).
- **`00-0F-AC:11`** — 802.1X + Suite-B-192.
- **`00-0F-AC:0B`** — 802.1X + SHA-256 (WPA3-Enterprise).
- **`00-0F-AC:0C`** — 802.1X + Suite-B-192-CNSA (WPA3-Enterprise
  192-bit mode).

## EAP outer methods (what the AP + RADIUS pick)

| method       | tunnel   | cert-based? | inner methods         |
| ------------ | -------- | ----------- | --------------------- |
| EAP-TLS      | TLS      | mutual      | (none — cert IS auth) |
| EAP-TTLS     | TLS      | server-only | PAP, CHAP, MSCHAPv2   |
| PEAPv0       | TLS      | server-only | MSCHAPv2, GTC         |
| PEAPv1       | TLS      | server-only | GTC (or MSCHAPv2)     |
| EAP-FAST     | TLS(PAC) | optional    | MSCHAPv2, GTC         |
| EAP-PWD      | none     | none        | (Dragonfly PAKE — CVE-2019-9497/9498/9499, CVE-2022-23303/23304) |
| LEAP         | none     | none        | MSCHAPv1              |
| EAP-MD5      | none     | none        | (plaintext CHAP)      |
| EAP-SIM/AKA  | (celllar)| SIM cred    | (3GPP-side)           |

Records: `eap_methods.json` — `eap-tls`, `eap-ttls`, `eap-peap`,
`eap-fast`, `eap-pwd`, `eap-leap`, `eap-md5`, `eap-sim`, `eap-aka`,
`eap-gtc`, `eap-peap-mschapv2`, `eap-peap-gtc`, `eap-ttls-pap`,
`eap-ttls-chap`, `eap-ttls-mschapv2`, `eap-fast-mschapv2`,
`eap-fast-gtc`, `eap-tls-1-3`, `eap-ikev2`, `eap-eke`.

## Inner-method downgrade — the attack surface

A rogue RADIUS advertises multiple outer methods and, once a TLS
tunnel opens, offers **weak inner methods**. A supplicant with lax
policy accepts the weaker offer.

Downgrade paths:

- **PEAP → MSCHAPv2** — capture challenge/response, crack with
  hashcat 5500 or asleap.
- **PEAP → GTC** — client sends a *plaintext token* (RSA OTP, Duo
  push code, static password). Value = flag surface.
- **EAP-TTLS → PAP** — client sends a *plaintext password*.
- **EAP-FAST → MSCHAPv2** — same as PEAP downgrade.

## Cert validation — the other attack surface

Even with EAP-TLS or PEAP, if the client does not validate the
RADIUS server certificate against a pinned CA / CN, a rogue-RADIUS
with any cert succeeds. Common failure modes:

- No CA pinning (client trusts any cert signed by a public CA).
- No CN pinning (client trusts wrong CN).
- User "Trust and continue" prompt on iOS / Android.
- Windows domain profile with `Do not validate server certificate`
  checked by the user or misconfigured by admin.

## MSCHAPv2 — the persistent weak link

Once you have a MSCHAPv2 challenge/response pair (from PEAP-MSCHAPv2
or TTLS-MSCHAPv2 inside a rogue tunnel), the crack is offline:

- **hashcat 5500** — direct NetNTLMv1-family crack.
- **asleap** — the original Cisco LEAP cracker; still works on
  MSCHAPv2 output.
- **`chapcrack` / cloudcracker** (2012 vintage) — DES-collision-
  based; not needed post-hashcat-5500 but historically referenced.

### MSCHAPv2 ChallengeHash derivation (shared callout)

`hashcat -m 5500` and `asleap` both expect an 8-byte `ChallengeHash`,
**not** the raw 16-byte `PeerChallenge` seen on the wire. hostapd-wpe
and freeradius-wpe pre-derive `ChallengeHash` for you; operators
reading a raw pcap must derive it themselves.

Given the three MSCHAPv2 inputs (RFC 2759 §8.1):

```
ChallengeHash = SHA1(PeerChallenge || AuthenticatorChallenge || Username)[:8]
```

- `PeerChallenge` — 16 bytes, sent by the client in the MSCHAPv2
  Response.
- `AuthenticatorChallenge` — 16 bytes, sent by the server in the
  MSCHAPv2 Challenge.
- `Username` — ASCII, no realm suffix.
- Take the first 8 bytes of the SHA-1 digest.

The canonical hashcat 5500 input format is a single line per
capture, four colon-separated fields:

```
user::domain::<NTResponse_hex>:<ChallengeHash_hex>
```

- `user` — inner-EAP identity.
- `domain` — realm / SSID / empty; not used cryptographically.
- `NTResponse_hex` — 24-byte MSCHAPv2 NTResponse, hex-encoded.
- `ChallengeHash_hex` — the 8-byte derived value above, hex-encoded.

Every tool walkthrough in this corpus that touches mode 5500
(hostapd-wpe, freeradius-wpe, asleap, hashcat, eaphammer) references
this callout — do not re-derive by hand from a pcap unless you
control the derivation and can verify it against a known-good
capture.

## MDM profile theft

A separate variant: after rogue-RADIUS association, the client's
device-management engine offers to (re)install a WiFi profile that
embeds a *device credential* — SCEP cert, PKINIT, whatever. Capture
the profile push, extract the cred. See
`attacks.json:mdm-profile-theft-captive-portal`.

## Cite

- IEEE Std 802.1X-2020.
- RFC 3748 — Extensible Authentication Protocol (EAP) framework.
- RFC 4137 — State machine for EAP peer and authenticator.
- RFC 5216 — EAP-TLS.
- RFC 5281 — EAP-TTLSv0.
- RFC 2759 — Microsoft PPP CHAP Extensions, Version 2 (MSCHAPv2).
- RFC 2865 — Remote Authentication Dial-In User Service (RADIUS).
- RFC 3579 — RADIUS Support For Extensible Authentication Protocol
  (EAP).
- RFC 7170 — Tunnel Extensible Authentication Protocol (EAP-TEAP)
  Version 1.
- RFC 9190 — EAP-TLS 1.3.
- Gabriel Ryan — eaphammer talks (DEFCON, BSides).
- Wright — `asleap` (hacking-exposed-wireless-3e).
- CVE-2022-23303, CVE-2022-23304 — hostapd/wpa_supplicant EAP-pwd
  memory-safety bugs; see also `dragonblood-deep/reference.md`.
- attacks.json: `rogue-radius-hostapd-wpe`,
  `rogue-radius-eaphammer`,
  `cert-phish-eaphammer-weak-validation`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-inner-downgrade-peap-gtc`,
  `mschapv2-challenge-response-capture`,
  `hashcat-5500-mschapv2-crack`,
  `asleap-mschapv2-crack`,
  `eap-gtc-plaintext-token-capture`,
  `mdm-profile-theft-captive-portal`,
  `leap-legacy-crack`.
