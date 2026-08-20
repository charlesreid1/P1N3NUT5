# hostapd reference

The AP daemon underneath every rogue AP we stand up. Runs on the
Pineapple over SSH via `do_create_rogue_ap`; also runs on any
laptop with a supported adapter.

## Skeleton config

```
interface=wlan0
driver=nl80211
ssid=RogueNet
hw_mode=g              # 'a' for 5 GHz, 'g' for 2.4 GHz
channel=6
country_code=US        # required for 5 GHz; harmless on 2.4 GHz
ieee80211d=1           # advertise country IE — hostapd refuses many 5 GHz chans without this
bssid=aa:bb:cc:dd:ee:ff   # optional; omit for adapter default
```

Add one of the security blocks below. Every full config should carry
the `country_code` + `ieee80211d=1` pair, even for 2.4 GHz — without
them hostapd rejects many 5 GHz channels outright and clients treat
missing Country IEs as a fingerprint.

## Security modes

### Open

```
# no wpa= line — that's open
```

### WPA2-PSK

```
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=YourPassphrase
```

### WPA2-Enterprise (rogue RADIUS pointing at another host)

```
wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP
ieee8021x=1
auth_server_addr=127.0.0.1
auth_server_port=1812
auth_server_shared_secret=radiussecret
```

Point `auth_server_addr` at freeradius-wpe or eaphammer's RADIUS.

### WPA3-SAE + PMF-required

```
wpa=2                      # yes, still wpa=2 — the AKM below flips it
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
sae_password=YourPassphrase
ieee80211w=2               # PMF required
```

### WPA3 transition mode (mixed)

```
wpa=2
wpa_key_mgmt=WPA-PSK SAE   # both AKMs
rsn_pairwise=CCMP
wpa_passphrase=YourPassphrase
sae_password=YourPassphrase
ieee80211w=1               # PMF optional
```

## Driver quirks per chipset

- **mac80211 / ath9k** — reference implementation. Everything works.
- **ath10k / ath11k** — some firmware revs mishandle beacon-interval
  changes on the fly; edit config and restart hostapd rather than
  hot-reloading.
- **mt76** — solid for AP mode; injection quirks discussed in
  chipsets/.
- **Realtek 88XX (rtl8812au etc.)** — hostapd works with aircrack-ng
  driver fork; stock kernel driver is often AP-mode-only or wonky.

## The alternative: hostapd-mana

`hostapd-mana` is a hostapd fork adding per-STA probe-response
(the MANA attack). See `karma-family/` for the semantics; use the
same config skeleton plus:

```
enable_mana=1
mana_loud=1                # broadcast union of seen probes
```

## Cite

- w1.fi hostapd source and hostapd.conf reference.
- Wi-Fi Alliance WPA3 Specification (SAE config knobs).
- SensePost hostapd-mana fork README.
