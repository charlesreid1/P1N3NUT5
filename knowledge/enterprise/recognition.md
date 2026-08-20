# enterprise — recognition

**Verified against:** hostapd 2.10 / freeradius 3.0.x / hashcat 6.2.x as of 2026-Q3

Distinguish enterprise from PSK by the RSN IE, then predict which
inner method a client will negotiate by initial-EAP fingerprint.

## Is this WPA-Enterprise?

RSN IE AKM Suite List. Look for any of:

- `00-0F-AC:01` — 802.1X (WPA2-Enterprise, legacy).
- `00-0F-AC:03` — FT-802.1X (with 802.11r).
- `00-0F-AC:05` — 802.1X + SHA-256.
- `00-0F-AC:0B` — WPA3-Enterprise.
- `00-0F-AC:0C` — WPA3-Enterprise 192-bit (Suite-B-192-CNSA).
- `00-0F-AC:11` — 802.1X + Suite-B-192.

## What outer EAP method is a client offering?

Capture an EAP-Request/Identity from the AP and the EAP-Response
from the client. The Method byte in the EAP-Response tells you.

| method byte | outer method    |
| ----------- | --------------- |
| 4           | EAP-MD5         |
| 6           | EAP-GTC         |
| 13          | EAP-TLS         |
| 17          | LEAP (Cisco)    |
| 18          | EAP-SIM         |
| 21          | EAP-TTLS        |
| 23          | EAP-AKA         |
| 25          | EAP-PEAP        |
| 43          | EAP-FAST        |
| 52          | EAP-PWD         |
| 55          | EAP-AKA'        |

Wireshark filter: `eap.type`.

## Which inner method will PEAP downgrade to?

Once the outer TLS tunnel opens, the RADIUS offers an inner EAP
method. Modern MDM policies pin this; weaker or older configs allow
any. Downgrade priority:

1. **EAP-GTC** — plaintext token; instant flag.
2. **EAP-MSCHAPv2** — challenge/response; crack with hashcat 5500.
3. **EAP-MD5** — plaintext-equivalent; instant crack.

`eaphammer --negotiate weakest` presents these in ascending
strength to see what the client will accept.

## Distinguishing cert validators from non-validators

- **Cert validator** — EAP-TLS never completes when the rogue
  presents an untrusted cert; you see repeated EAP-Failure or a
  clean disassoc after the ServerHello.
- **Non-validator** — TLS handshake completes with your cert;
  inner-EAP begins. This is the vulnerable client.
- **Mixed** — some clients (older Android, unmanaged Windows)
  prompt the *user* to "trust and continue." User behavior
  variable.

## ANQP realm hints (pre-association intel)

If the AP supports 802.11u/Interworking, an ANQP query for element
261 (NAI Realm) returns realms the AP recognizes. This tells you
what identity the target expects.

```
wpa_cli -i wlan0 anqp_get <BSSID> 261
```

See `hotspot2/walkthrough.md`.

## Cite

- IEEE Std 802.1X-2020.
- RFC 3748 — EAP method type registry.
- attacks.json: `eap-inner-downgrade-peap-gtc`,
  `eap-inner-downgrade-peap-mschapv2`,
  `cert-phish-eaphammer-weak-validation`.
