# airgeddon — walkthrough

Menu-driven TUI in the same class as wifite2, but with a stronger
captive-portal / evil-twin workflow built in. Reach for it when you
want a one-shot evil-twin engagement without hand-editing hostapd.

## Preconditions

- airgeddon installed (`apt install airgeddon` on Kali or clone
  the git repo).
- Monitor+injection adapter.
- Optional: rockyou.

## Path A — Baseline engagement

```
sudo airgeddon
```

Menu navigation:

1. **Interface** → select the monitor-capable adapter.
2. **Put interface in monitor mode.**
3. **Attack menu** — options include:
   - WPS attacks
   - WPA/WPA2 attacks (handshake + PMKID)
   - **Evil Twin attacks** (with 5 sub-modes)
   - Enterprise attacks
   - DoS

## Path B — Evil-twin captive-portal engagement

airgeddon's evil-twin menu is its strongest feature. Sub-modes:

1. **Just AP.**
2. **AP with sniffing (Ettercap-in-the-middle).**
3. **AP with sniffing + SSLstrip.**
4. **AP with sniffing + SSLstrip + BeEF hook.**
5. **AP with captive portal (cred capture).**

Sub-mode 5 is the WCTF favorite. airgeddon:

- Brings up hostapd with the target SSID + BSSID.
- Runs dnsmasq for DHCP.
- Runs a PHP-based captive portal on the rogue interface.
- Deauths the target off the real AP.
- Validates the submitted passphrase against a captured 4-way
  handshake (like fluxion).

## Path C — Enterprise attack

airgeddon wraps hostapd-wpe:

```
# Menu path:
#   Enterprise attacks → Certificate creation → Wildcard portal
```

Ships a pre-baked hostapd-wpe workflow with cert-CN spoofing.

## Path D — Read the output

```
ls ~/airgeddon/
# captured/handshake_*.cap
# captured/psk_*.txt         # cracked PSKs
# captured/enterprise_*.log  # captured MSCHAPv2 lines
```

## Where airgeddon stops (compared with hand-driven paths)

Same wall as wifite2:

- **PMF-required networks.** Deauth doesn't push clients.
- **WPA3-SAE.** Not part of the workflow.
- **SSID Confusion, Framing Frames, MacStealer, Wi-Fi 7 MLO.** Not
  supported.
- **Default-PSK derivation.** No SSID-regex handling.
- **Hotspot 2.0 / ANQP.** No.

Use airgeddon as a fast first-pass. Escalate to hand-driven paths
when it says "no handshake" or the target isn't its shape.

## Failure modes

- **TUI freezes.** Some airgeddon versions ship without `dialog` on
  certain distros. `apt install dialog`.
- **Menu paths differ between versions.** Different git tags rename
  submenus. Read the current version's help.
- **Evil-twin sub-mode 5 loops the "wrong password" prompt.** Target
  hasn't typed the real passphrase yet. Verify with:
  `aircrack-ng -w candidate.txt /path/to/handshake.cap`.
- **Deauth ineffective.** PMF-required. See PMF section of `deauth/`.

## Cite

- v1s1t0r1sh3r3/airgeddon GitHub.
- attacks.json: `evil-twin-clone`, `captive-portal-cred-capture`,
  `rogue-radius-hostapd-wpe`, `pmkid-capture`,
  `wpa2-4way-capture`.
