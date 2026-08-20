# fluxion — reference

**Verified against:** fluxion `master` (FluxionNetwork/fluxion) as of 2026-Q3

Fluxion is a captive-portal-phishing tool built for laptop-based
engagements. It chains deauth → evil twin → captive portal →
PSK-guess validation via a captured handshake. Popular among CTF
beginners because it's mostly menu-driven; less popular in production
because its layout assumes a laptop, not a purpose-built AP.

Read this alongside `captive-portal/` and `evil-twin/` — the same
chain, packaged for one shell.

## Attack chain

```
1. Capture a 4-way handshake from the target AP (deauth + airodump).
2. Bring up a rogue AP on the target SSID (BSSID clone, open network).
3. Start dnsmasq + DNS-hijack + HTTP portal on the rogue.
4. Serve a vendor-branded "reauth" login page in the client's browser.
5. When a client enters a passphrase, validate it against the
   captured handshake (aircrack-ng offline check).
6. If it matches, the "flag" is the passphrase.
```

The **captured-handshake validation** step is what distinguishes
Fluxion from plain evil-twin cred phishing: the user's typed
passphrase is instantly checked against the offline handshake, so
Fluxion refuses wrong guesses and keeps asking. This raises success
rate against users who make typos.

## Directory layout (github.com/FluxionNetwork/fluxion)

```
fluxion/
├── fluxion.sh                        main menu driver (sudo ./fluxion.sh)
├── language/                         top-level localized string files
├── attacks/                          one directory per attack module
│   ├── Captive Portal/
│   │   ├── attack.sh
│   │   ├── language/                 attack-local translations
│   │   └── sites/                    portal templates per vendor
│   └── Handshake Snooper/
│       ├── attack.sh
│       └── handshakes/               captured 4-way handshakes land here
├── lib/                              helpers sourced by fluxion.sh
└── logos/                            vendor branding assets
```

Validation chain: the Captive Portal attack requires a handshake
under `attacks/Handshake Snooper/handshakes/`; if none exists,
fluxion invokes Handshake Snooper first, then feeds the resulting
`.cap` back into the portal's `aircrack-ng`-based validator.

## Comparison with P1N3NUT5's native path

| step         | fluxion                       | native (P1N3NUT5)                       |
| ------------ | ----------------------------- | --------------------------------------- |
| capture      | airodump + aireplay (laptop)  | hcxdumptool on the Mark VII             |
| rogue AP     | hostapd on the laptop         | hostapd on the Pineapple's wlan1        |
| DHCP/DNS     | dnsmasq (laptop)              | dnsmasq or PineOS built-in              |
| portal       | fluxion sites/ templates      | evil-portal module / custom             |
| validation   | aircrack-ng offline check     | trial-decrypt via `post-crack-rf`       |
| ergonomics   | menu-driven, one shell        | scripted, MCP-native                    |
| deniability  | none                          | Pineapple hides in a backpack           |

Fluxion is faster to start; P1N3NUT5 is faster to run repeatedly and
integrates with the MCP tools.

## When to reach for fluxion at a WCTF

- **You have a laptop and no Pineapple.** Fluxion works.
- **A specific WCTF puzzle explicitly asks you to reproduce a
  fluxion-style engagement.** Rare but happens.
- **Otherwise:** prefer `captive-portal/walkthrough.md` +
  `evil-twin/walkthrough.md` on the Pineapple.

## Cite

- FluxionNetwork/fluxion GitHub — README, attack.sh scripts.
- aircrack-ng documentation — the underlying handshake-validation
  step (`aircrack-ng -w <candidate.txt> capture.cap`).
- attacks.json: `evil-twin-clone`, `captive-portal-cred-capture`,
  `wpa2-4way-capture`.
