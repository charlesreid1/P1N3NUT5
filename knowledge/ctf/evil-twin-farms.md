# Evil-twin farms — which one is the trap?

## The puzzle shape

WCTF drops you in a room where 3–10 APs advertise the same SSID
(e.g. `WCTF-GUEST`). One is the legitimate flag-serving AP; the
others are traps. Associating to a trap gets you a fake flag or
blacklists you from scoring for N minutes.

## Recognition — spot the odd one out

Use `beacon_diff` (Phase 4 tool). Diff every AP's beacon against
every other AP's beacon. The signals that distinguish the real one:

- **IE order.** Legitimate APs of the same firmware family emit
  IEs in a consistent order. A rogue built with hostapd will emit
  a different order — hostapd puts Vendor-Specific IEs after
  Extended Capabilities, most consumer firmware does the reverse.
- **Vendor-Specific IE list.** Consumer routers advertise
  Microsoft WPA1 vendor IE + WPS + a manufacturer-specific IE. A
  hostapd rogue usually only has WPS.
- **Beacon interval / DTIM.** Consumer firmware defaults to 100
  TU / DTIM 2. hostapd defaults to 100 TU / DTIM 2 too — but many
  operators change this in their `hostapd.conf`.
- **Rate set.** Real APs typically advertise every rate from 1 to
  54 Mbps. Rogues sometimes omit low rates.
- **WPS Manufacturer / Model.** Real Cisco vs. `hostapd-mana` says
  everything.

## Recognition — spot the real one differently

Alternately: watch which BSSID legitimate clients associate to
over time. `list_associations` will surface it — a real
scorebot-driven client keeps returning to the real AP.

## When to build your own

If the puzzle wants you to *become* the evil twin (capture what a
victim client sends when it lands on you), use `do_evil_twin` with
`deauth_clients=True` to knock clients off the real AP.

## Cite

- attacks.json: `evil-twin-clone`.
- knowledge/evil-twin/reference.md.
