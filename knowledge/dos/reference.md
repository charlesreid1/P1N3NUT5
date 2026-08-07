# DoS families — beyond broadcast deauth

Broadcast deauth is one member of a bigger family. Every mode below
is either useful as an attack primitive on its own or a decoy /
flag-signal in a WCTF puzzle.

## mdk4 mode catalog

| mode | attack |
| ---- | ------ |
| `d` | Deauth flood (broadcast or targeted) |
| `a` | Authentication flood (fills AP auth table) |
| `p` | Probe request flood (from spoofed clients) |
| `b` | Beacon flood (fake APs — every SSID in a list) |
| `v` | RTS/CTS NAV manipulation |
| `m` | Michael MIC countermeasure (TKIP-only; forces 60s AP shutdown) |
| `e` | EAPOL-Start flood (against 802.1X authenticator) |
| `f` | Fuzzed beacon / probe response frames |

## Other primitives

- **EAPOL-Start flood** — target the RADIUS backend; each Start
  provokes an EAP-Request from the authenticator. Fill the state
  table.
- **Association-request flood** — targets the AP's association
  table. Some APs cap total STAs and reject legitimate ones.
- **TIM / DTIM poisoning** — see `framing-frames/` for the queued-
  frame variant.
- **CTS-to-self silencing** — send CTS-to-self with a long NAV
  duration; every neighbor stays quiet for the duration. Repeat.
- **Malformed IE crash-boots** — some client stacks OOM on giant
  Vendor-Specific IEs in a beacon. Vendor-specific; historical but
  not gone.

## When a DoS is a flag signal, not a technique

Some WCTF scoring bots use "seen a Michael MIC failure" or "seen
CTS-to-self from BSSID X" as a *flag trigger* rather than a
disruption to avoid. Read the puzzle brief — if it lists a specific
frame pattern as the flag, the DoS attack is the flag-emitter,
not something to defend against.

## Cite

- aircrack-ng documentation — mdk4 modes.
- IEEE Std 802.11-2020 §9.4 (management frames), §11.2 (power
  management for TIM/DTIM), §9.3.2.6 (Michael MIC countermeasure).
- attacks.json: `deauth-broadcast`, `deauth-targeted`,
  `authentication-flood`, `association-flood`, `beacon-flood-mdk4`,
  `probe-flood-mdk4`, `rts-cts-nav-dos`, `cts-to-self-silencing`,
  `eapol-start-flood`, `tkip-michael-mic-dos`.
