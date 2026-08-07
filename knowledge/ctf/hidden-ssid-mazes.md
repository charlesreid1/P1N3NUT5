# Hidden-SSID puzzles

## The puzzle shape

An AP broadcasts with an empty SSID (SSID IE length 0). The flag
requires you to associate — but you need the SSID string to do
that. WCTF variants stack hidden SSIDs into a maze: the SSID for
AP #2 is only revealed once you associate to AP #1, etc.

## The recovery technique

The SSID is not a secret. Wait for a client to associate — its
Probe Request or Association Request carries the SSID plainly.

```
list_probe_requests(since_s=60)
# look for a probe request whose SSID field matches the
# hidden AP's BSSID's typical client pool
```

If no client is around, you can accelerate:

```
# Deauth-force a client that's already associated to the hidden
# AP; on reassociation it will Probe Request the SSID plainly.
do_deauth(bssid=<hidden-ap-bssid>, client_mac=<seen-client>,
          count=3, respect_pmf=True, i_own_the_airspace=True)
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

## Cite

- attacks.json: `wpa2-4way-capture`, `deauth-targeted`.
- knowledge/wpa2/recognition.md.
- verify_claim: "Hiding your SSID makes the network secret" →
  false.
