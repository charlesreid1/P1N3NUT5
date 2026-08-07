# pcap / pcapng — walkthrough

tshark one-liners for the analysis you actually run at a WCTF.
Everything below assumes an 802.11-radiotap capture. If your pcap
doesn't have radiotap, the header field references (`radiotap.*`)
won't work — capture with `hcxdumptool`, `airodump-ng`, or
`tcpdump -i wlan1mon -y IEEE802_11_RADIO` to get radiotap.

## Recipe A — Enumerate APs

```
tshark -r capture.pcapng \
  -Y "wlan.fc.type_subtype == 8" \
  -T fields -e wlan.bssid -e wlan.ssid \
              -e wlan.ds.current_channel -e radiotap.dbm_antsignal \
  | sort -u
```

## Recipe B — Enumerate STAs (probe requests)

```
tshark -r capture.pcapng \
  -Y "wlan.fc.type_subtype == 4" \
  -T fields -e wlan.sa -e wlan.ssid \
  | sort -u
```

## Recipe C — Handshake completeness check

Is there a full 4-way for a given target?

```
tshark -r capture.pcapng \
  -Y "eapol and wlan.bssid == AA:BB:CC:DD:EE:FF" \
  -T fields -e wlan.sa -e wlan.da -e eapol.type -e eapol.keydes.key_info
# Look for 4 rows alternating M1/M2/M3/M4.
```

## Recipe D — PMKID extraction

hcxpcapngtool does the heavy lifting; tshark confirms presence:

```
tshark -r capture.pcapng \
  -Y "eapol and wlan.rsn.ie.pmkid != 0" \
  -T fields -e wlan.sa -e wlan.da -e wlan.rsn.ie.pmkid
```

Then:

```
hcxpcapngtool -o hs.22000 capture.pcapng
grep '^WPA\*01' hs.22000
```

## Recipe E — Decrypt data frames (with recovered PSK)

The capture must contain the full 4-way handshake and every ESSID
the frames belong to.

```
tshark -r capture.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"wpa-pwd\",\"MyPassphrase:CorpWiFi\"" \
  -Y "http.request or dns" -V
```

Alternative key types: `wpa-psk` (64 hex PMK), `tk` (per-session TK),
`msk` (enterprise MSK).

## Recipe F — Filter capture down to one STA

```
tshark -r all.pcapng \
  -Y "wlan.addr == 11:22:33:44:55:66" \
  -w /tmp/sta.pcapng
```

## Recipe G — Extract all beacons for a channel

```
tshark -r all.pcapng \
  -Y "wlan.fc.type_subtype == 8 and wlan.ds.current_channel == 6" \
  -w /tmp/beacons-ch6.pcapng
```

## Recipe H — Beacon-diff (evil-twin spot)

```
# Two beacons, one from each candidate BSSID.
tshark -r all.pcapng -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:FF" -c 1 -V > /tmp/beacon-a.txt
tshark -r all.pcapng -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:00" -c 1 -V > /tmp/beacon-b.txt
diff /tmp/beacon-a.txt /tmp/beacon-b.txt
# Focus on RSN, Vendor-Specific, WPS Manufacturer.
```

## Recipe I — Deauth-storm forensics

```
# Rate + reason-code distribution.
tshark -r storm.pcapng \
  -Y "wlan.fc.type_subtype == 0x0c" \
  -T fields -e frame.time_relative -e wlan.sa -e wlan.fixed.reason_code

# Group by (source, reason):
tshark -r storm.pcapng -Y "wlan.fc.type_subtype == 0x0c" \
       -T fields -e wlan.sa -e wlan.fixed.reason_code \
  | sort | uniq -c | sort -rn
```

See `ctf/deauth-forensics.md` for interpretation.

## Recipe J — pcapng → classic pcap conversion

Some legacy tools (very old aircrack-ng builds) only speak classic
pcap.

```
editcap capture.pcapng capture.cap
```

## Recipe K — Split a big capture

```
editcap -c 100000 huge.pcapng chunk_.pcapng
```

Emits `chunk_00000.pcapng`, `chunk_00001.pcapng`, etc. Useful when a
capture is too big for Wireshark's memory ceiling.

## Recipe L — Merge captures

```
mergecap -w combined.pcapng one.pcapng two.pcapng
```

## Recipe M — Radiotap-only extraction (channel + RSSI)

```
tshark -r capture.pcapng \
  -T fields -e frame.time_relative \
              -e radiotap.channel.freq \
              -e radiotap.dbm_antsignal \
              -e wlan.sa
```

## Recipe N — Probe-request IE order fingerprinting

```
tshark -r capture.pcapng \
  -Y "wlan.fc.type_subtype == 4 and wlan.sa == 11:22:33:44:55:66" \
  -T fields -e wlan.tag.number \
  | head -30
```

Compare against `client_fingerprints.json`.

## Failure modes

- **`tshark: 'wlan.rsn.ie.pmkid' not a valid field name'`** —
  older tshark; upgrade or use `wlan.rsn.pmkid`.
- **`enable_decryption` yields garbage** — capture missing the
  4-way; verify with Recipe C.
- **`editcap` refuses format** — some pcapng writers emit
  non-standard block types; try Wireshark's "Save As" instead.
- **Slow analysis on multi-GB captures** — split with Recipe K.

## Cite

- Wireshark documentation — display filter reference.
- IEEE Std 802.11-2020 — frame formats.
- hcxtools GitHub.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`,
  `deauth-broadcast`, `deauth-targeted`, `evil-twin-clone`.
