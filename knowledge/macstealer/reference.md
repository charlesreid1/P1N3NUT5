# MacStealer

Vanhoef 2023, BlackHat Asia. Client-side flaw: when a WiFi client is
disconnected and later reconnects to the same network, some
implementations continue to accept frames destined for its previous
MAC. An attacker on the same network who knows the target's MAC can
hijack traffic returning to that MAC.

## Preconditions

- Attacker is on the same network as the victim (already has PSK, or
  the network is Open / OWE).
- Attacker knows the victim's MAC (easy — passive observation).
- Victim's client implementation is one of the affected ones.

## Cite

- Vanhoef 2023 — MacStealer slides (BlackHat Asia).
- attacks.json: `macstealer-mac-hijack`.
