# post-crack-rf — reference

## PSK → PMK → PTK chain (WPA2-Personal)

```
passphrase ──PBKDF2-HMAC-SHA1(4096, ESSID, 256b)──► PMK (32 bytes)

PMK + ANonce + SNonce + MAC_AP + MAC_STA ──PRF──► PTK (48 or 64 bytes)
                                                    │
                                                    ├── KCK (16 B) — MIC key
                                                    ├── KEK (16 B) — GTK wrap key
                                                    └── TK  (16 or 32 B) — data cipher key
```

For WPA3-SAE the PMK is derived from the SAE exchange, not PBKDF2,
so knowing the passphrase alone doesn't reproduce the PMK — you also
need the SAE Commit/Confirm bytes from the actual session.

## What Wireshark actually needs to decrypt

- **PSK-based decryption** — requires the passphrase, the ESSID, and
  *all four* EAPOL messages for each STA whose traffic you want to
  decrypt. Wireshark re-runs the derivation using the ANonce/SNonce
  from the captured 4-way.
- **PMK-based decryption** — if you know the PMK directly (rare;
  useful when you have SAE PMK dumps). Wireshark accepts a
  `wpa-psk` key entry that is the 64-hex-char PMK.

## Key entry formats (Wireshark IEEE 802.11 protocol prefs)

| type      | value                              |
| --------- | ---------------------------------- |
| wpa-pwd   | `passphrase:ESSID`                 |
| wpa-psk   | 64 hex chars (the PMK)             |
| tk        | 32 hex chars (TK) — decrypts data  |
|           | with no need for the 4-way frames  |
| msk       | up to 128 hex chars (MSK, Enterprise) |

The `tk` entry is what you use when you have a per-session decrypt
target (e.g. a Kr00k tail-frame decrypt with the known-zero TK).

## Joining as a STA — wpa_supplicant vs. iwd

Both are valid; `wpa_supplicant` is universal, `iwd` is the modern
systemd-native default on Fedora, Arch, and some IoT.

`wpa_supplicant` minimal config:

```
network={
    ssid="CorpWiFi"
    key_mgmt=WPA-PSK
    psk="<cracked passphrase>"
}
```

Then: `wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/target.conf`.

`iwd` uses `.psk` files under `/var/lib/iwd/`:

```
# /var/lib/iwd/CorpWiFi.psk
[Security]
Passphrase=<cracked passphrase>
```

Then: `iwctl station wlan0 connect CorpWiFi`.

## Extracting the 4-way handshake for a specific STA

`hcxpcapngtool` and `tshark` can filter captures down to a single
STA-to-AP session:

```
hcxpcapngtool -o /tmp/hs.22000 --essid=CorpWiFi capture.pcapng
tshark -r capture.pcapng \
       -Y "eapol && (wlan.sa == 11:22:33:44:55:66 || wlan.da == 11:22:33:44:55:66)" \
       -w /tmp/single-sta.pcapng
```

Wireshark's decrypt logic uses whichever complete 4-way it can
match. Multiple 4-ways for multiple STAs in one pcap = all of them
decrypt if the PSK is right.

## Enterprise (MSK-based) decryption

For WPA2/3-Enterprise captures, the 4-way is seeded from the MSK the
EAP exchange produced. If you have the MSK (e.g. from a rogue-RADIUS
capture where hostapd-wpe logged it), Wireshark's `msk` key entry
decrypts.

The MSK is per-session — every association produces a new one.

## Cite

- IEEE Std 802.11-2020, §12.7 (Key management).
- Wireshark docs — wpa-pwd / wpa-psk / tk / msk key entry formats.
- hcxtools GitHub.
