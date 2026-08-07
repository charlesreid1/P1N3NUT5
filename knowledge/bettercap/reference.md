# bettercap — WiFi module

The Swiss army knife's WiFi module. Runs directly on the Pineapple's
OpenWRT userland or on a laptop. Less specialized than hcxtools, but
better session ergonomics and a real REPL / API surface.

## Modules we use

```
wifi.recon on                  # start scanning
wifi.recon.channel 6           # lock to a channel
wifi.recon.channel clear       # channel-hop again
wifi.assoc <BSSID>             # attempt PMKID capture via assoc request
wifi.deauth <BSSID>            # deauth (only if PMF is off)
wifi.handshakes                # show captured 4-way handshakes
wifi.client.probe <STA>        # inject probe request from spoofed MAC
wifi.ap <ssid> <bssid> <ch> <enc>   # spin up a rogue AP inline
```

Session state persists in `~/.bettercap` — `session.save handshakes.session`,
`session.load handshakes.session`.

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
