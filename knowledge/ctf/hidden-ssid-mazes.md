# Hidden-SSID puzzles

**Verified against:** P1N3NUT5 knowledge corpus as of 2026-Q3

## The puzzle shape

An AP broadcasts with an empty SSID (SSID IE length 0). The flag
requires you to associate — but you need the SSID string to do
that. WCTF variants stack hidden SSIDs into a maze: the SSID for
AP #2 is only revealed once you associate to AP #1, etc.

## The recovery technique

The SSID is not a secret. Wait for a client to associate — its
Probe Request or Association Request carries the SSID plainly.

`list_probe_requests` is a real MCP tool — `server.list_probe_requests()`
(takes no `since_s`; filter the returned payload client-side).
`do_deauth` is a real MCP tool.

```python
list_probe_requests()
# filter the payload for a probe request whose SSID field matches the
# hidden AP's client pool.
```

If no client is around, you can accelerate:

```python
# Deauth-force a client that's already associated to the hidden AP;
# on reassociation it will Probe Request the SSID plainly.
do_deauth(bssid="<hidden-ap-bssid>", client_mac="<seen-client>",
          count=3, respect_pmf=True, i_own_the_airspace=True)
```

**Fallback (no MCP):**

```bash
# passive — capture probe requests naming the hidden BSSID's pool
sudo tcpdump -i wlan1mon -w /tmp/probes.pcap \
    "type mgt subtype probe-req"
tshark -r /tmp/probes.pcap \
    -Y "wlan.fc.type_subtype == 0x04 && wlan.ssid" \
    -T fields -e wlan.sa -e wlan.ssid | sort -u

# active — targeted deauth to force a reassoc (PMF-off only)
sudo aireplay-ng -0 3 -a <hidden-ap-bssid> -c <seen-client> wlan1mon
```

## Failure modes

- **PMF-required.** The deauth doesn't land. Wait passively for a
  natural reassoc.
- **Modern iOS/Android with per-SSID randomization.** The client
  still names the SSID in the probe — MAC randomization does not
  hide SSID.
- **No client has ever associated in your capture window.**
  Nothing to reveal. Move on.

## Do NOT do

- Waste time treating the hidden SSID as security. It is not. The
  IE is left blank in beacons only; every other frame that
  references the network carries the name.

## What still works when PMF-required

The optional acceleration step above uses `do_deauth` to force a
re-association whose Probe/Association Request leaks the SSID.
When the hidden AP is PMF-required or on 6 GHz, the deauth is a
no-op — but the SSID recovery is not actually blocked, because
the SSID isn't a secret:

- **Passive wait.** `list_probe_requests` alone finds the SSID
  whenever any client either roams, wakes from sleep, or first
  associates. No deauth needed. Extend the dwell to minutes on a
  quiet room.
- **Karma probe attraction.** Broadcast an empty SSID pool with
  Known Beacons off; you don't need to lure — you just want the
  target's *own* probing to hit your monitor. See
  `karma-family/walkthrough.md`.
- **RSSI-dominant twin on a wildcard SSID.** Some clients
  Probe-Request the hidden SSID by name when they see a stronger
  BSSID that they've associated to before. Twin the BSSID (with
  a different SSID) and watch the probe traffic.
- **Client leaks the SSID in the M2 of a natural 4-way.** The
  Association Request already carries the SSID plainly; PMF
  protects mgmt frames but not the *contents* of the SSID IE.
  Any natural reassoc — even to the real AP — leaks it.

## Cite

- attacks.json: `wpa2-4way-capture`, `deauth-targeted`,
  `pineap-passive-probe-log`.
- knowledge/wpa2/recognition.md.
- knowledge/ctf/pmf-required-targets.md.
- verify_claim: "Hiding your SSID makes the network secret" →
  false.
