# post-crack-rf — walkthrough

**Verified against:** hashcat 6.2.x + tshark 4.2 as of 2026-Q3

## Path A — Decrypt a captured pcap

You have a `.pcapng` and a PSK. Recover the plaintext data frames.

```
# Preconditions: capture contains the full 4-way handshake between
# the target AP and at least one STA; ESSID is known.

# Wireshark (GUI):
#   Edit → Preferences → Protocols → IEEE 802.11
#   [x] Enable decryption
#   Decryption keys → +
#       key type: wpa-pwd
#       value:    <passphrase>:<ESSID>
#   Apply. Reopen the capture.

# CLI:
tshark -r capture.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"wpa-pwd\",\"MyPassphrase:CorpWiFi\"" \
  -Y "http.request or dns" -V
```

If decryption succeeded, `-Y "http.request"` returns HTTP payloads
from data frames that had been encrypted at capture time. WCTF flag
surfaces: HTTP host headers, DNS query names, MQTT payloads.

## Path B — Validate a candidate PSK

You have a candidate passphrase and want to confirm without
associating (which would deauth other clients or leave logs).

```
# Take any existing capture that has a 4-way for the target ESSID.
# Try to decrypt one data frame.

tshark -r capture.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"wpa-pwd\",\"CandidatePassword:CorpWiFi\"" \
  -Y "wlan.fc.type == 2 and data" \
  -c 5
```

If frames decrypt (LLC/SNAP headers visible, sensible protocols in
the payload), the passphrase is right. If frames stay opaque, the
passphrase is wrong. This is faster and quieter than trial
association.

## Path C — Join as a legitimate STA

The last-mile validation. You want the Pineapple (or a laptop)
associated to the target with the recovered PSK.

```
# wpa_supplicant path
cat > /etc/wpa_supplicant/target.conf <<EOF
ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
    ssid="CorpWiFi"
    key_mgmt=WPA-PSK
    psk="<recovered passphrase>"
}
EOF

wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/target.conf
dhclient wlan0
ip addr show wlan0
```

Confirm the association actually completed:

```
wpa_cli -i wlan0 status
# wpa_state=COMPLETED means the 4-way completed.
```

## Path D — Extract a specific STA's PTK from an existing pcap

Wireshark can decrypt globally, but you can also extract a *specific*
PTK from a captured 4-way for use with `tk` key entries elsewhere
(e.g. correlating with an isolated later capture).

```
# Filter down to one STA:
tshark -r all.pcapng \
       -Y "eapol && wlan.addr == 11:22:33:44:55:66" \
       -w /tmp/sta.pcapng

# Wireshark decrypt with wpa-pwd, note the derived PTK from the
# `Decryption keys` log. Reuse via `tk` entries on future captures.
```

## Path E — Verify the flag is the PSK itself

Many WCTF puzzles use "the PSK is the flag." Confirmation:

- Recovered passphrase matches the expected flag format
  (`flag{...}`, `CTF{...}`).
- Recovered PSK passes Path B decryption on a known-good pcap.
- Associating with Path C succeeds.

If all three, the flag is done. **Stop.**

## Failure modes

- **Decrypt yields garbage.** Wrong PSK; wrong ESSID casing; capture
  missing 4-way. Verify with `tshark -r capture.pcapng -Y "eapol"`
  that all four EAPOL messages are present for the target STA.
- **Association fails, 4-way MIC error.** Wrong PSK.
- **Association succeeds but no DHCP.** The AP or the wired uplink
  is filtering your MAC (common on WCTF setups). Try a different
  STA MAC; the association is verified either way.
- **iwd instead of wpa_supplicant on the target platform.** Same
  passphrase; different config file (`.psk` under
  `/var/lib/iwd/`).

## Cite

- IEEE Std 802.11-2020, §12.7.
- Wireshark IEEE 802.11 protocol preference documentation.
- hostapd + wpa_supplicant documentation (w1.fi).
- iwd documentation (git.kernel.org/pub/scm/network/wireless/iwd).
- attacks.json: `wpa2-4way-capture`, `pmkid-capture`.
