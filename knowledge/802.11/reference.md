# 802.11-2020 rollup — quick reference

## Session lifecycle

```
Beacon ────────── AP announces (broadcast, ~10× / sec)
   │
Probe Request ─── Client asks "who's on this channel?"
Probe Response ── AP unicasts back its beacon-equivalent
   │
Auth Req/Resp ─── 802.11 auth (formality for WPA2; carries SAE for WPA3)
   │
Assoc Req/Resp ── Client joins; RSN IE selects cipher + AKM
   │
4-way handshake ─ EAPOL M1..M4 derives PTK (WPA2/3-PSK) or ties to MSK
   │                 (WPA2/3-Enterprise); M1 optionally carries PMKID
   │
Data frames  ──── CCMP/GCMP encrypted user traffic
   │
Deauth / Disassoc  Terminates session; reason codes carry state
```

## Frame types

- **Management (type 0)** — beacon, probe req/resp, auth, (re)assoc,
  deauth, disassoc, action. See `frame_types.json` for byte layout;
  action frames carry 11k/11v/11r payloads.
- **Control (type 1)** — RTS, CTS, ACK, block-ack. NAV manipulation
  is a legitimate MAC feature and a DoS surface.
- **Data (type 2)** — user frames, QoS-data (most common), null-data
  (power-save state), and the LLC/SNAP EtherType 0x888E carrier for
  EAPOL-Key.

## Key hierarchy (WPA2/3-Personal)

```
PSK   ── PBKDF2-HMAC-SHA1(passphrase, ESSID, 4096, 256) ── PMK  (WPA2)
                                                         │
Anonce + Snonce + MAC_AP + MAC_STA + PMK ── PRF ─────────┤
                                                         ▼
                                                        PTK
                                       ┌──── KCK  (MIC over EAPOL)
                                       ├──── KEK  (encrypts GTK during M3)
                                       └──── TK   (data cipher key, CCMP/GCMP)
```

WPA3-SAE derives the PMK from the SAE commit/confirm exchange, not
PBKDF2 over the passphrase — that's why offline-PSK crack doesn't apply
directly to WPA3.

## PMF (802.11w) coverage

Protected: deauth, disassoc, most robust action frames.
Not protected: management frames before the 4-way completes, all
control frames, some action-frame categories (BTM in some
implementations — see `attacks.json:btm-forced-roam`).

## Cite

- IEEE Std 802.11-2020, §5, §9 (frames), §12 (security), §13 (roaming).
