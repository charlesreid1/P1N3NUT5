# wifite2 — the auto-orchestrator

Beginner-friendly WiFi-audit orchestrator: enumerate APs, pick the
weakest, try WPS Pixie, fall back to WPS PIN brute, fall back to
PMKID, fall back to 4-way + deauth, feed hashcat. Everything from one
`wifite --dict rockyou.txt` command line.

## What wifite2 automates

- Monitor-mode setup (via `airmon-ng`).
- WEP crack path (still bundled).
- WPS attacks (Reaver + Bully + Pixie via `pixiewps`).
- PMKID capture via `hcxdumptool`.
- 4-way capture via `airodump-ng` + targeted `aireplay-ng`.
- Hashcat handoff (or feed to `aircrack-ng --wpa`).

## Where wifite2 stops

- **PMF-required networks.** Deauth silently fails and wifite2 does
  not know to pivot to Kr00k / SSID Confusion.
- **WPA3-only networks.** No fallback path — wifite2 does not
  implement Dragonblood or SAE-specific attacks.
- **WPA3 transition mode.** Wifite2 sees the SAE AKM in the RSN IE
  and skips the AP; it does not know to attack the WPA2 side.
- **Enterprise (802.1X).** Not supported.
- **Vendor default-PSK derivation.** Not supported.
- **Beacon-IE stego, ANQP recon, hidden-SSID mazes.** Not the tool's
  problem class.

## Rule of thumb

An assistant using this MCP should **beat wifite2 on any target
wifite2 handles**, because our tools cover the same ground with
better observability, AND **know when wifite2 will fail** so it
does not become the crutch on tricky targets.

## Cite

- wifite2 GitHub (kimocoder fork is the maintained one in 2026).
