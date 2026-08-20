# Kr00k — all-zero PTK on disassoc

Broadcom / Cypress WiFi chipsets (and later a Qualcomm Atheros variant)
have a bug in their firmware disassociation handler: when a STA sees
a disassoc, any frames still in the encryption queue are transmitted
using an **all-zero pairwise transient key** rather than being dropped.
An attacker who can capture the tail-frame handful on the air can then
decrypt them offline with a known zero key.

## Trigger + affected chipsets

- **CVE-2019-15126** — Broadcom BCM4339/4358/4356, Cypress inheritors.
  Trigger: attacker sends a spoofed disassoc frame; victim's chipset
  flushes its pending encryption queue with PTK=0.
- **CVE-2020-3702** — Qualcomm Atheros variant. IPQ8064, QCA9377,
  Snapdragon-family Wi-Fi front-ends. Same primitive, longer patch tail.

## Affected devices in 2026

Flagship phones are patched. The tail lives on:

- Older Amazon Echo / Kindle
- WiFi cameras (Wyze, Amcrest, cheap OEM)
- Older iPhone / iPad revs on end-of-life iOS
- Older Raspberry Pi WiFi HATs on Cypress chips
- Many IoT hubs / smart-home bridges

## Byte-level primitive

The vulnerable code path is inside the chipset firmware's disassoc
handler, not the host OS. Sequence:

1. STA's chipset holds an encryption queue keyed by the current PTK
   (16-byte TK for CCMP-128, 32-byte for GCMP-256).
2. Attacker sends a **spoofed unprotected disassoc** targeting the
   STA. The chipset processes it before the host OS reacts.
3. The disassoc handler zeroes the TK (writes 16 or 32 zero bytes)
   but does NOT flush the pending TX queue.
4. The TX loop draws the next frame from the queue and encrypts it
   with the now-zero TK, then transmits.
5. Attacker in monitor mode captures the tail frames (typically 1–8
   frames depending on queue depth) and decrypts offline using an
   all-zero key.

For Wireshark decrypt, the UAT `80211_keys` entry must use key type
`tk` (not `wpa-psk`) with 16 hex zeros for CCMP-128 or 32 hex zeros
for GCMP-256 / CCMP-256:

```
"tk","00000000000000000000000000000000"       # CCMP-128
"tk","0000000000000000000000000000000000000000000000000000000000000000"  # GCMP-256
```

## Detection surface

A live victim leaks Kr00k tail frames every time it disassocs (with
or without attacker prompting). Passive monitoring — no injection
required:

```
tshark -r cap.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"tk\",\"00000000000000000000000000000000\"" \
  -Y "wlan.fc.type_subtype == 0x0A and radiotap.rxflags.badfcs == 0" -V
```

Look for a burst of encrypted data frames in the ~50 ms following
each disassoc. If Wireshark decrypts them (readable IP header, DHCP
option, HTTP GET), the target is vulnerable.

## Cite

- ESET 2020 — Kr00k white paper + detector release.
- CVE-2019-15126, CVE-2020-3702.
- attacks.json: `kr00k-broadcom-cve-2019-15126`, `kr00k-qca-cve-2020-3702`.
- knowledge/records/cves.json: `cve-2019-15126`, `cve-2020-3702`.
- knowledge/records/chipset_vulns.json — full chipset matrix.
