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

## H2E (Hash-to-Element) — signaled via RSNXE, not AKM

Dragonblood mitigation. Replaces the "hunt-and-peck" PWE (password
element) loop with Hash-to-Element (SAE-PT construction). The hunt
loop's timing oracle disappears.

**How H2E is signaled on the wire.** Per WFA WPA3 Specification and
IEEE 802.11-2020 §9.4.2.241 RSNX Element: the **RSN Extension
Element (RSNXE, IE 244)** carries an "SAE Hash-to-Element only" bit
(bit 5 of the RSNX Capabilities field). H2E is enabled by that bit —
it is NOT a distinct AKM number. Any SAE AKM (AKM 8 or AKM 24) can
use H2E if both peers set the RSNXE bit; conversely an AKM 8 client
without RSNXE runs hunt-and-peck.

## SAE-EXT-KEY (AKM 24, 0x18) — extended-key derivation

Per IEEE 802.11-2020 Table 9-151: AKM 24 (wire byte `00-0F-AC:18`)
= SAE-EXT-KEY. This AKM extends the SAE PMK-derivation KDF to
384-bit output for use with GCMP-256 pairwise cipher (WPA3-Enterprise
192-bit-suite compatibility). SAE-EXT-KEY implies H2E, but H2E does
not imply SAE-EXT-KEY. Do not confuse the two.

**Common mistake.** AKM decimal-vs-hex: AKM 18 = 0x12 = OWE (not
SAE-EXT-KEY). AKM 24 = 0x18 = SAE-EXT-KEY. Every beacon-selector byte
in the corpus follows this rule; see [[akm-selector-glossary]] and
records/security_suites.json.

## PMF-required

WPA3-Personal and WPA3-Enterprise both require 802.11w PMF-required in
the beacon (MFPR bit set). Broadcast deauth doesn't reach the client.

## Transition mode (the door left open)

RSN IE carries **both** AKM 2 (PSK) and AKM 8 (SAE). Intended for
mixed fleets during rollout. Attack: your rogue AP advertises WPA2-only,
the client fails-over, its WPA2 4-way is captured, and the WPA2 PSK is
the WPA3 password. See `attacks.json:wpa3-transition-downgrade`.

## OWE (Opportunistic Wireless Encryption) — WPA3 companion

Not SAE, but ships alongside WPA3 as the "no-password but still
encrypted" option (AKM 18 = `00-0F-AC:12`). OWE runs an anonymous
Diffie-Hellman inside the association exchange; every client-AP pair
gets a distinct PMK. Transition-mode OWE advertises both an OWE BSS
and an open (unencrypted) BSS with matching BSS IDs so legacy clients
still associate. That transition mode is exactly the door
CVE-2021-30004 (wpa_supplicant OWE candidate-selection race) walks
through: a supplicant with an OWE transition profile can be nudged
onto the open sibling BSS by a rogue AP that suppresses the OWE
beacon, downgrading to unencrypted.

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
- RFC 8110 — Opportunistic Wireless Encryption (OWE).
- CVE-2021-30004 — wpa_supplicant OWE transition-mode downgrade race.
