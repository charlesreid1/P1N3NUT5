# Multi-Channel MitM — walkthrough

**Verified against:** hostapd 2.11 (Vanhoef 2018 PoC) as of 2026-Q3

Two radios, one victim. The Pineapple Mk VII's dual-radio hardware is
exactly what this primitive assumes. This is the substrate for KRACK,
FT-handshake capture, SSID Confusion in the presence of band-steering,
and generally any evil twin that needs a *different* channel from the
real AP.

## Preconditions

- Pineapple Mk VII (or any two-radio host) with `wlan0` capable of
  2.4 GHz monitor+injection and `wlan1` capable of 5 GHz likewise.
- Legitimate AP identified: SSID, BSSID, channel.
- Victim client identified: MAC, current channel.

## Setup

Bring up `wlan0` as a STA on the *real* AP's channel and `wlan1` as
the *rogue AP* on a different channel with the same SSID+BSSID.

```
# radio 1 — the real-side STA (attacker-as-client)
iw dev wlan0 set type managed
wpa_supplicant -i wlan0 -c /etc/wpa_supplicant/real-network.conf &

# radio 2 — the rogue AP (attacker-as-AP), different channel
cat > /tmp/rogue.conf <<EOF
interface=wlan1
driver=nl80211
ssid=CorpWiFi
bssid=AA:BB:CC:DD:EE:FF        # clone of the real BSSID
hw_mode=g
channel=11                     # DIFFERENT from real AP's channel (say 6)
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=<PSK if known>
EOF
hostapd /tmp/rogue.conf &
```

The victim's driver, seeing the clone AP on ch 11 with a stronger RSSI
than the real AP on ch 6, roams.

## Forwarding

To keep the association working while you MitM, bridge the two radios:

```
# create a bridge; add the STA side and the AP side
brctl addbr br-mitm
brctl addif br-mitm wlan0
brctl addif br-mitm wlan1
ip link set dev br-mitm up
```

The victim now sees `wlan1` as its AP; the real AP still sees `wlan0`
as a legitimate client. Every frame in either direction traverses your
kernel.

## Why "multi-channel"

A single-radio evil twin on the *same* channel as the real AP has a
collision problem — the real AP's frames stomp on yours. Different
channels means the victim's radio no longer hears the real AP at all
(driver stays locked to the strongest AP on the currently-scanned
channel). The real AP still hears you *as a normal STA* — because you
are one.

## Downstream attacks this unlocks

- **KRACK.** The KRACK primitive requires channel-based MitM to
  intercept the M3 retransmit. See `krack-client-key-reinstall`.
- **FT-handshake capture.** If the target roams (11k neighbor report +
  11v BTM), you can force the FT reassoc to occur through you.
- **SSID Confusion.** If the target's client trusts SSID X on one band
  and Y on another, MC-MitM lets you serve the SSID that maximizes
  policy leakage. See `ssid-confusion-cve-2023-52424`.
- **Straight evil twin with credential capture.** Once traffic
  traverses you, all the usual TLS-strip / captive-portal / cred-cap
  attacks apply.

## Failure modes

- **PMF-required, no downgrade.** Broadcast deauth can't push the
  victim toward you; you rely on RSSI-based roam. Position matters.
- **Band-steering AP.** A modern AP may steer the client back to its
  preferred band once RSSI equalizes. Match the AP's band-steering
  IE (see `attacks.json:band-steering-abuse`).
- **BSSID collision.** Cloning the exact BSSID sometimes trips a WIDS
  or the client's driver. Try cloning to a BSSID that differs by one
  bit; some clients tolerate that as a "second AP on the same ESSID."

## Cite

- Vanhoef & Piessens 2017 — KRACK, §3 (MC-MitM setup).
- attacks.json: `mc-mitm-dual-radio`,
  `krack-client-key-reinstall`, `band-steering-abuse`,
  `ssid-confusion-cve-2023-52424`.
