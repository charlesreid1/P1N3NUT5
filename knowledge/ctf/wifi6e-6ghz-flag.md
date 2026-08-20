# Wi-Fi 6E — flag lives on a 6 GHz-only AP

Enumerate 6 GHz targets from 2.4/5 GHz Reduced Neighbor Reports, then
associate (or attack) on 6 GHz if your radio can tune it.

## Recognition

2.4/5 GHz beacons carry an RNR IE (IE 201) advertising 6 GHz neighbor
BSSIDs. Operating class 131–137 = 6 GHz. WPA3-only mandate — the RSN
IE on the 6 GHz side will list AKM 8 (SAE) or AKM 24 (SAE-EXT-KEY);
never AKM 2.

## The one-shot sequence

```python
run_sequence([
    # 1. Passive capture 2.4 + 5 GHz.
    {"action": "recon_start", "band": "abg", "dwell_ms": 250},
    {"action": "wait", "s": 20},
    {"action": "recon_stop"},

    # 2. Enumerate 6 GHz targets from RNR IEs.
    {"action": "list_rnr_neighbors",
     "src_pcap": "/tmp/recon.pcapng",
     "out": "/tmp/6ghz_targets.json"},

    # 3. If a 6 GHz card is available, associate directly and attack.
    #    Otherwise, look for a 2.4/5 GHz side of the same ESSID.
    {"action": "match_essid_across_bands",
     "essid": "<target ESSID>",
     "want_band": "2.4 or 5"},

    # 4. WPA2/3 transition on 2.4/5 side if it exists — attack there.
    {"action": "capture_pmkid",
     "bssid": "<the-2.4-BSSID>",
     "timeout_s": 45},
])
```

## MCP mapping / fallback

- `recon_start` / `recon_stop` → `server.recon_start` / `server.recon_stop`.
- `capture_pmkid` → `server.do_capture_pmkid`.
- `list_rnr_neighbors`, `match_essid_across_bands` — **not in `src/`**.
  Parse from the pcap manually.

**Fallback shell chain — RNR enumeration:**

```bash
# RNR is IE 201 (0xC9). Wireshark dissects it as wlan.tag.number == 201.
tshark -r /tmp/recon.pcapng \
       -Y "wlan.fc.type_subtype == 8 && wlan.tag.number == 201" \
       -T fields -e wlan.bssid -e wlan.tag.number \
       -e wlan.rnr.tbtt_info.bssid -e wlan.rnr.tbtt_info.oper_class \
       -e wlan.rnr.tbtt_info.channel \
  | sort -u > /tmp/6ghz_targets.tsv

# Match ESSID across bands — group beacons by SSID, filter operating-class 131..137
tshark -r /tmp/recon.pcapng \
       -Y "wlan.fc.type_subtype == 8" \
       -T fields -e wlan.ssid -e wlan.bssid -e wlan.ds.current_channel \
  | sort -u
```

## The flag surface

- **RNR IE payload itself** — some WCTF puzzles hide the flag in the
  neighbor report's SSID Config or vendor-specific extensions.
- **Data traffic on the 6 GHz side** — requires a 6 GHz-capable radio
  (ath11k, mt76 with a 6E-capable module, rtw89).
- **Passphrase shared across 6/5/2.4 sides** — if the network has
  a 2.4/5 GHz transition side, the PSK is the same on 6 GHz.

## What if you have no 6 GHz radio?

- **RNR recon still works** without a 6 GHz radio (Path A of the
  6E walkthrough). If the flag is in the RNR itself, you're done.
- **Cross-band PSK.** Attack the 2.4/5 GHz side and the recovered PSK
  probably lets you decrypt any 6 GHz side captures a teammate does
  later.
- **Passpoint / OI-based association.** If the 6 GHz AP is
  Passpoint-configured, a matching Roaming Consortium OI in a rogue
  beacon on 2.4/5 GHz can lure clients away.

## Failure modes

- **No RNR IE in 2.4/5 GHz beacons.** Some cheap 6E gear omits it
  despite the MUST. Direct 6 GHz scan is the only path; needs a
  6 GHz radio.
- **6 GHz side is truly WPA3-only + PMF-required + AKM 24.** Attack
  surface reduces to Dragonblood side channels (`dragonblood-deep`)
  or waiting for a bad implementation.
- **6 GHz operating class not supported by your driver.** Even with
  a 6E-capable card, monitor mode may not extend across the full
  UNII-5..8 range.

## Cite

- attacks.json: `rnr-6ghz-enumeration`,
  `wpa3-transition-downgrade`, `dragonblood-*`.
- IEEE Std 802.11ax-2021.
- Wi-Fi Alliance — Wi-Fi CERTIFIED 6E requirements.
