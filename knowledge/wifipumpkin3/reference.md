# wifipumpkin3 — reference

WiFiPumpkin3 is the modern successor to WiFi-Pumpkin. It's a
Python-based rogue-AP framework with a plugin system and captive-
portal templating. The main draw is the templating ecosystem —
WP3 ships dozens of pre-authored portals that can be dropped into
the Pineapple's `evil-portal` module with light adaptation.

Read this alongside `captive-portal/` and `evil-twin/`.

## Architecture

```
wifipumpkin3
├── core/                 # AP driver, DHCP/DNS/HTTP dispatch
├── plugins/              # captive portal, sniffers, DNS spoofer
├── proxys/               # SSLStrip, transparent HTTP proxy
├── modules/              # sub-tools (extension points)
├── templates/            # captive-portal HTML+PHP templates
│   ├── phishing_ap/
│   │   ├── microsoft/
│   │   ├── google/
│   │   ├── linkedin/
│   │   ├── router/       # generic ISP router
│   │   ├── starbucks/
│   │   └── xfinity/
```

## Plugins that matter for WCTF

| plugin           | what it does                                      |
| ---------------- | ------------------------------------------------- |
| `dns_spoof`      | DNS interception + resolver hijack                |
| `captiveflask`   | Serves captive portal via Flask                   |
| `sniffkin3`      | HTTP/HTTPS credential sniffing (SSLStrip-family)  |
| `pumpkinproxy`   | Transparent proxy for arbitrary payload injection |
| `karma`          | Probe-response KARMA                              |

## Template format

Each template dir has:

```
templates/phishing_ap/<vendor>/
├── captive.html
├── captive.js
├── captive.css
├── assets/            # logos, favicons
└── login.php          # form handler (writes to log)
```

Templates are portable — they can be copied into the Pineapple's
evil-portal module directory or served by any HTTP framework.

## Comparison with fluxion

| trait            | wifipumpkin3            | fluxion                         |
| ---------------- | ----------------------- | ------------------------------- |
| Language         | Python 3                | Bash                            |
| Interface        | REPL-style CLI          | Menu-driven                     |
| Templates        | ~15 built-in, plugin-extensible | ~5 built-in, harder to extend |
| Handshake check  | via `aircrack-ng` if configured | Built-in, automatic          |
| Fits on Pineapple| Yes with Python 3.9+    | Yes but with more overhead      |

## When to reach for WP3

- **You want a specific vendor's captive portal replica** and WP3
  has it.
- **You want SSLStrip-style downstream payload injection** on
  associated traffic.
- **You're building a custom evil-portal module** and want to steal
  WP3's template HTML.

## Cite

- WiFiPumpkin3 GitHub (P0cL4bs / mh4x0f).
- attacks.json: `evil-twin-clone`, `captive-portal-cred-capture`.
