# bettercap — WiFi module

**Verified against:** bettercap 2.32.0

The Swiss army knife's WiFi module. Runs directly on the Pineapple's
OpenWRT userland or on a laptop. Less specialized than hcxtools, but
better session ergonomics and a real REPL / API surface.

## Modules we use

```
wifi.recon on                             # start scanning
set wifi.recon.channels 6                 # lock recon to channel 6
set wifi.recon.channels 1,6,11,36,44,149  # hop across a fixed list
set wifi.recon.channels ""                # clear the list, hop freely
wifi.assoc <BSSID>                        # PMKID capture via assoc req
wifi.deauth <BSSID>                       # deauth (only if PMF is off)
set wifi.handshakes.file /tmp/handshakes.pcap  # where captures land
set wifi.handshakes.aggregate true             # 1 file, all targets
set wifi.ap.ssid EvilTwin                 # rogue-AP SSID
set wifi.ap.bssid AA:BB:CC:DD:EE:FF       # rogue-AP BSSID
set wifi.ap.channel 6                     # rogue-AP channel
set wifi.ap.encryption false              # open (or true for WEP)
wifi.ap                                   # start the rogue AP
```

There is no bare `wifi.handshakes` command; handshakes stream into
the file set by `wifi.handshakes.file` and are surfaced in
`wifi.show`. Bettercap listens passively for client probe requests
in `wifi.recon on`; there is no dedicated `wifi.client.probe`
injector — use `mdk4 p`/`aireplay-ng -9` for injected probes.

State is saved by loading a caplet (`load caplet-name`) rather than a
`session.save`/`session.load` pair; write reusable playbooks in
`~/.bettercap/caplets/*.cap` and reload them at will.

## When to use bettercap over hcxtools + aireplay

- **REPL workflow.** You are hunting live and want to iterate: recon,
  see a client, `wifi.assoc` it, check handshakes, deauth again.
- **Scripting.** Bettercap has a Lua-esque caplet system for saved
  playbooks.
- **Not for.** Aggressive multi-target capture — hcxdumptool is
  faster and better-filtered. Long-running captures should still go
  through hcx.

## Cite

- bettercap GitHub.
- attacks.json: `wpa2-4way-capture`, `pmkid-capture`,
  `deauth-broadcast`.
