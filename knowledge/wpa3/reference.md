# WPA3 reference — SAE, H2E, transition mode

## SAE (Simultaneous Authentication of Equals)

Replaces WPA2's PBKDF2-passphrase-to-PMK with a Dragonfly-family
password-authenticated key exchange. Passwords no longer feed a fixed
KDF; each association derives a fresh PMK from a Diffie-Hellman-style
commit/confirm.

```
STA                                         AP
 │  Commit  = (scalar, Peer-Commit-Element) │
 ├──────────────────────────────────────────►
 │                                          │
 │  Commit                                  │
 ◄──────────────────────────────────────────┤
 │                                          │
 │  Confirm = MIC over commit elements      │
 ├──────────────────────────────────────────►
 │  Confirm                                 │
 ◄──────────────────────────────────────────┤
                    ▼
                   PMK (32 bytes)
                    │
                    ▼
              4-way handshake (same shape as WPA2)
```

The 4-way still runs — the AP has to prove it knows the PMK too — but
the PMK is now unique per session, so capturing 4-way frames gains
you nothing offline.

## H2E / SAE-EXT-KEY (AKM 18)

Dragonblood mitigation. Replaces the "hunt-and-peck" PWE (password element)
loop with Hash-to-Element (SAE-PT construction). The hunt loop's timing
oracle disappears. `RSN AKM 00-0F-AC:18` is the H2E variant; presence in
the beacon means the AP supports the mitigated construction.

## PMF-required

WPA3-Personal and WPA3-Enterprise both require 802.11w PMF-required in
the beacon (MFPR bit set). Broadcast deauth doesn't reach the client.

## Transition mode (the door left open)

RSN IE carries **both** AKM 2 (PSK) and AKM 8 (SAE). Intended for
mixed fleets during rollout. Attack: your rogue AP advertises WPA2-only,
the client fails-over, its WPA2 4-way is captured, and the WPA2 PSK is
the WPA3 password. See `attacks.json:wpa3-transition-downgrade`.

## 6 GHz — WPA3-only mandate

Wi-Fi 6E (6 GHz, UNII-5..8) mandates WPA3-Personal or WPA3-Enterprise.
No transition mode. This closes the WPA2 downgrade door on the 6 GHz
band — but Dragonblood-style side channels still apply where the SAE
implementation is weak.

## Cite

- IEEE Std 802.11-2020, §12.4 (SAE).
- Wi-Fi Alliance WPA3 Specification.
- Vanhoef & Ronen 2019 — Dragonblood.
- RFC 7664 — Dragonfly.
