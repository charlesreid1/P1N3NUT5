# Evil-twin farms — which one is the trap?

## The puzzle shape

WCTF drops you in a room where 3–10 APs advertise the same SSID
(e.g. `WCTF-GUEST`). One is the legitimate flag-serving AP; the
others are traps. Associating to a trap gets you a fake flag or
blacklists you from scoring for N minutes.

## Recognition — spot the odd one out

Use `beacon_diff` — real MCP tool: `server.beacon_diff(bssid_a,
bssid_b, pcap_path)` (see `src/p1n3nut5_mcp/server.py`; wraps
`detect.beacon_diff`). Diff every AP's beacon against every other AP's
beacon. The signals that distinguish the real one:

- **IE order.** Legitimate APs of the same firmware family emit
  IEs in a consistent order. A rogue built with hostapd will emit
  a different order — hostapd puts Vendor-Specific IEs after
  Extended Capabilities, most consumer firmware does the reverse.
- **Vendor-Specific IE list.** Consumer routers advertise
  Microsoft WPA1 vendor IE + WPS + a manufacturer-specific IE. A
  hostapd rogue usually only has WPS.
- **Beacon interval / DTIM.** Consumer firmware defaults to 100
  TU / DTIM 2. hostapd defaults to 100 TU / DTIM 2 too — but many
  operators change this in their `hostapd.conf`.
- **Rate set.** Real APs typically advertise every rate from 1 to
  54 Mbps. Rogues sometimes omit low rates.
- **WPS Manufacturer / Model.** Real Cisco vs. `hostapd-mana` says
  everything.

## Recognition — spot the real one differently

Alternately: watch which BSSID legitimate clients associate to
over time. `list_associations` (real MCP tool:
`server.list_associations`) will surface it — a real scorebot-driven
client keeps returning to the real AP.

**Fallback (no MCP) — beacon IE diff via tshark:**

```bash
# List IEs for each beacon; compare BSSIDs pairwise.
for bssid in AA:BB:CC:DD:EE:01 AA:BB:CC:DD:EE:02; do
  echo "=== $bssid ==="
  tshark -r /tmp/recon.pcapng \
      -Y "wlan.fc.type_subtype == 8 && wlan.bssid == $bssid" \
      -T fields -e wlan.tag.number -e wlan.tag.length \
      -e wlan.tag.oui | sort -u | head -30
done
```

## When to build your own

If the puzzle wants you to *become* the evil twin (capture what a
victim client sends when it lands on you), use `do_evil_twin` (real
MCP tool: `server.do_evil_twin(target_bssid, target_ssid,
target_channel, deauth_clients=True, i_own_the_airspace=True)`).

## What still works when PMF-required

The "spot the odd one out" recognition side of this puzzle is
independent of PMF — beacon-IE diffing works whether the real AP
is MFPR=1 or not; beacons are unprotected by design.

The *become the trap* variant (`do_evil_twin` with
`deauth_clients=True`) does depend on deauth. When the real AP
is PMF-required or 6 GHz:

- **Beat the real AP on RSSI + wait.** Skip the deauth; a louder
  twin wins natural reassociations.
- **Karma-family attraction (Known Beacons + MANA).** Attracts
  cold-start probing clients regardless of PMF; see
  `karma-family/walkthrough.md`.
- **BTM-forced roam.** If the vendor honors unauth'd BTM
  Requests, hint the target toward your rogue.
- **Cert-phish enterprise farms.** If the farm advertises
  WPA-EAP, cold-start clients associating for the first time
  don't have any PMF context — the rogue-RADIUS harvest lands
  without a deauth.

## Cite

- attacks.json: `evil-twin-clone`, `btm-forced-roam`,
  `mana-known-beacons`.
- knowledge/evil-twin/reference.md.
- knowledge/ctf/pmf-required-targets.md.
