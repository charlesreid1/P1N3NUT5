# kismet — walkthrough

**Verified against:** kismet 2023-07-R1

The passive-collection workhorse. Long-running, database-backed,
alert-driven. Reach for it when you want to collect an
uninterrupted picture of an RF environment for hours, and query it
later with SQL.

Note: the `kismet_server`/`kismet_client` split was retired in the
2019 rewrite. Everything below drives the single `kismet` binary.

## Preconditions

- Kismet server + client installed (`apt install kismet` on Kali).
- Root or `kismet` group membership (for iface capture).
- Monitor-mode-capable adapter.
- Optional: GPS dongle for wardriving.

## Path A — Server + Web UI on the Pineapple

```
# On the Pineapple over SSH:
opkg update && opkg install kismet
# (Skip if the community module already ships it.)

# Start (single binary; -c takes a source, repeatable):
kismet -c wlan1mon
```

Web UI on `http://172.16.42.1:2501/` (kismet's default). Log in with
the credentials set in `/root/.kismet/kismet_httpd.conf`.

## Path B — Long-form passive capture

Kismet channel-hops across all configured bands; every observed
device lands in the database.

```
# Configure sources for a big capture (2.4 + 5 GHz on separate
# interfaces).
# /root/.kismet/kismet_site.conf:
source=wlan0:name=r1-2g
source=wlan1:name=r2-5g
hop_channels=1,6,11,36,44,52,60,100,116,149,161

kismet -c wlan0mon -c wlan1mon
```

## Path C — GPS wardriving

```
# Attach GPS dongle (USB serial, gpsd)
apt install gpsd gpsd-clients
systemctl start gpsd

# In kismet_site.conf:
gps=gpsd:host=localhost,port=2947

# Start capture. Every observed AP is tagged with lat/lon.
```

Export to Wigle-compatible format:

```
kismetdb_dump_devices --in kismet.log \
                      --format csv \
                      --out targets.csv
```

## Path D — Query the .kismet DB

Kismet's DB is SQLite. The real tables are `devices`, `packets`,
`data`, `alerts`, `messages`, and `snapshots`. The `devices` row's
per-device state is stored in a JSON blob in the `device` column;
scalar columns cover time / signal / geo only. There is no
`avg_signal` column and no `probed_ssids` table — probed SSIDs live
inside `device` under `$.dot11.device.probed_ssid_map`.

Signal fields on `devices` are `min_signal`, `max_signal`,
`avg_signal_dbm` (JSON — inside the blob) and the scalar
`strongest_signal`. Use `strongest_signal` for a stable RSSI sort.

```
sqlite3 kismet.log <<'SQL'
.mode column
.headers on
SELECT devkey, phyname, devmac, first_time, last_time, strongest_signal
FROM devices
WHERE type = 'Wi-Fi AP'
  AND devmac LIKE '00:03:7F:%'          -- Atheros OUI
ORDER BY strongest_signal DESC
LIMIT 20;
SQL
```

Common queries (all against the JSON blob via `json_extract`):

```
-- All clients probing for a specific SSID.
-- probed_ssid_map is an object keyed by SSID hash; iterate with json_each.
SELECT d.devmac, je.value AS probed_ssid
FROM devices d,
     json_each(json_extract(d.device,
                            '$.dot11.device.probed_ssid_map')) je
WHERE je.value = 'CorporateGuest';

-- Every SSID a given client has ever probed for.
SELECT je.value AS ssid
FROM devices d,
     json_each(json_extract(d.device,
                            '$.dot11.device.probed_ssid_map')) je
WHERE d.devmac = 'AA:BB:CC:DD:EE:FF';

-- Mobile devices — seen at >1 rounded geo cluster.
SELECT devmac,
       COUNT(DISTINCT ROUND(avg_lat, 3) || '/' || ROUND(avg_lon, 3)) AS locs
FROM devices
GROUP BY devmac
HAVING locs > 5;
```

If `json_extract` returns `NULL`, the device blob wasn't fully
populated (short capture window or non-802.11 phy). Fall back to
`json_extract(device, '$.dot11.device.last_probed_ssid_csum')` +
matching against `dot11.device.advertised_ssid_map` on APs to link
probes to observed SSIDs.

## Path E — Alerts / WIDS engine

Kismet's alert engine fires on:

- **DEAUTHFLOOD** — high-rate deauth from one source.
- **KARMA** — an AP probe-responding to too many distinct SSIDs.
- **EVILTWIN** — two beacons with the same SSID but different BSSIDs
  and inconsistent capabilities.
- **CRYPTOCHANGE** — an AP's advertised cipher/AKM changed.
- **BSSTIMESTAMP** — beacon-timestamp anomaly.

Query alerts:

```
SELECT ts_sec, header, brief FROM alerts;
```

## Path F — Replay-mode analysis

Feed kismet a pcap; it runs the alert engine as if live.

```
kismet --no-ncurses \
       --source=pcapfile:capture.pcapng \
       --log-prefix=/tmp/replay
```

Useful for post-CTF forensics on someone else's dump.

## Failure modes

- **Web UI 404s after login.** Version mismatch between the
  packaged server and installed plugins. Reinstall.
- **Kismet says "no monitor iface".** NetworkManager or wpa_supplicant
  is fighting. `airmon-ng check kill`.
- **Very slow.** Kismet writes to disk aggressively; use a
  fast SD card or point `log_prefix` at USB storage.
- **Alert firing too often.** Tune the trigger thresholds in
  `kismet_alerts.conf`.

## When to reach for kismet

- **First-60-seconds recon** at a con where you want a persistent DB.
- **Wardriving** with GPS integration.
- **WIDS-style operational awareness** on a long engagement.
- **Post-engagement analysis** — the .kismet DB is a full audit
  trail.

## When NOT to

- **Fast one-shot capture** — hcxdumptool or `airodump-ng` is
  simpler.
- **Attack orchestration** — kismet is a passive collector; attacks
  are hostapd/hcx-tools/mdk4 territory.

## Cite

- kismetwireless.net documentation.
- attacks.json: `pineap-passive-probe-log`,
  `evil-twin-clone` (kismet detects the attack, doesn't fire it).
