# Evil twin reference

## The primitive

Bring up a rogue AP that matches a target AP on every observable field:

- **SSID** (from the Beacon's SSID IE)
- **BSSID** (from the Beacon's Address 2)
- **Channel** (from the DS Parameter Set IE)
- **RSN IE** (or lack thereof — matching security posture matters)
- **Vendor-Specific IEs** (WPS, Microsoft WPA1) — clients that
  fingerprint APs will notice differences here
- **Beacon interval / DTIM period** — some clients drop candidates
  whose beacon interval differs sharply

If your rogue BSSID beats the real AP on RSSI at the client, the client
associates with you. If not, deauth the client off the real AP and
your rogue is the next available beacon it hears.

## hostapd config skeleton

```
interface=wlan0
driver=nl80211
ssid=CorporateWiFi
hw_mode=g
channel=6
bssid=aa:bb:cc:dd:ee:ff

# WPA2-PSK evil twin
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=<what-you-think-it-might-be>

# For a WPA2-Enterprise evil twin, replace with:
# wpa_key_mgmt=WPA-EAP
# ieee8021x=1
# eap_server=1
# eap_user_file=/etc/hostapd/hostapd.eap_user
```

For the karma-family variants, use `hostapd-mana` which extends hostapd
with per-STA probe response.

## Detection perspective

An evil twin is spotted by:

- **IE-order diff** vs a known-good capture (`beacon_diff` in the MCP)
- **Chipset fingerprint** — WPS Manufacturer/Model leaks even when WPS
  is nominally disabled
- **BSSID collision** — a second beacon with the same BSSID on a
  different channel

## Cite

- IEEE Std 802.11-2020, §9.4.
- hostapd configuration reference (w1.fi).
- SensePost 2014 — MANA writeup.
