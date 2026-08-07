# kismet — the passive collector

Long-running passive-capture daemon with a REST API, a Web UI, GPS
integration, and a rich alert engine. Great for wardriving and for
first-60-seconds recon when you want a persistent database.

## Modes

- **Live** — attach one or more monitor interfaces; kismet channel-
  hops and captures.
- **Replay** — feed it a pcap; the alert engine still fires.

## Data model

Everything lands in a `.kismet` SQLite database:

- **`devices`** table — one row per observed BSSID and per client
  MAC. Includes seen-first, seen-last, RSSI history.
- **`packets`** — every frame, with radiotap metadata.
- **`alerts`** — WIDS-style triggers (KARMA responder, evil-twin,
  deauth flood, DEAUTHFLOOD, ADHOCONWATCHNET, and about 40 others).

## REST API

Kismet's REST API exposes queries against the DB in real time:

```
curl -s http://127.0.0.1:2501/system/status.json
curl -s http://127.0.0.1:2501/devices/last-time/-30/devices.json
curl -s http://127.0.0.1:2501/alerts/last-time/-30/alerts.json
```

The API is authenticated; log in through the WebUI once to seed
`~/.kismet/kismet_httpd.conf` with the credentials.

## When to reach for kismet

- Long recon window (hours+, especially with GPS).
- Passive-only engagement (you cannot transmit; kismet does not).
- WIDS-perspective — you want to know what your OWN attack looked
  like from a defender's console.

## Cite

- kismet documentation.
- attacks.json: `pineap-passive-probe-log` (Pineapple's built-in
  passive log covers the same ground for shorter windows).
