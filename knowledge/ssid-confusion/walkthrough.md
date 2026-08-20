# SSID Confusion walkthrough

**Verified against:** hostapd 2.11 + tshark 4.2 as of 2026-Q3

Two networks, same PSK. Client believes it's on network X. It's on Y.
The client's higher-layer policy (VPN, per-SSID trust) responds to the
wrong signal.

## Setup

Two APs — the legitimate one (SSID X) is out of your control; the
rogue one (SSID Y) you stand up:

```
# rogue hostapd — SSID Y, but the same PSK as SSID X

interface=wlan0
driver=nl80211
ssid=GuestNet                # SSID Y
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=SharedPassword123    # same PSK as SSID X (CorpWiFi)
```

The trick is that when the client's supplicant completes the 4-way
handshake it derives a PTK that depends on the PMK + nonces + MAC
addresses. Both SSIDs share a PSK, so the PMK is identical. The client
succeeds — and its higher layers (VPN toggle, WiFi trust prompt) read
the SSID string, which the attacker chose freely.

## Steps

1. **Confirm shared PSK.** The attack does not work without it. If
   the client has separate credentials per SSID, this attack is not
   applicable.
2. **Bring up the rogue on the SSID the client's policy trusts less**
   (e.g. GuestNet). Ensure your BSSID + channel are attractive on RSSI.
3. **Force the client toward you.** Options:
   - Deauth off the legitimate SSID (works only if PMF is not required).
   - Rely on natural roam if the client is moving.
   - Combine with MC-MitM if band-steering is in play.
4. **The client associates.** Its supplicant sees "GuestNet" in the
   beacon. Its VPN policy or MDM engine sees "GuestNet" — and if that
   SSID triggers different behavior than the legitimate SSID (e.g.
   "turn VPN off on CorpWiFi, on for everything else" — but backwards),
   the flag surface opens.
5. **Read the client's traffic** via the rogue AP just like an
   evil-twin capture. In a WCTF, the flag is often what the client
   sends when it believes it is on the trusted network — an
   authorization header, a policy check-in, a preference sync payload.

## Failure modes

- **PSKs differ.** Not applicable.
- **Client's WPA supplicant validates BSSID + SSID combination
  against its stored profile.** Some 2025+ Linux iwd builds do; most
  Android and iOS do not, as of the 2024 paper.
- **Client uses per-SSID randomization AND fresh MAC.** The attack
  still works — the primitive is about SSID string trust at higher
  layers, not MAC identity.

## Cite

- Héloïse Gollier and Mathy Vanhoef, "SSID Confusion: Making Wi-Fi
  Clients Connect to the Wrong Network" (2024, KU Leuven / DistriNet).
  CVE-2023-52424, co-disclosed 2024-05-14.
- attacks.json: `ssid-confusion-cve-2023-52424`.
