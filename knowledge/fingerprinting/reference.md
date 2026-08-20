# Client fingerprinting

Modern OS clients randomize their MAC — but they leak on other axes.

## Signals that identify a client

- **Probe-request IE order.** Different OS supplicants emit their IE
  list in different orders. iOS is very consistent; Windows varies
  with the driver; Android varies with the OEM. See
  `client_fingerprints.json` for the per-OS profiles.
- **Extended-Capabilities bit pattern.** Which capability bits (11k
  neighbor report, 11v BTM, TDLS, etc.) a client advertises is a
  strong OS+version signature.
- **Supported-rates set.** Some OS builds omit low rates that the
  standard says every 802.11g client should send.
- **Vendor-Specific IEs.** Apple emits IE 0x0017F2; Samsung emits
  its own; Cisco emits Aironet-family IEs. Even under a randomized
  MAC, the vendor IE persists.
- **Sequence-number continuity.** The 12-bit Sequence Control counter
  is not always reset when the MAC randomizes. Two frames with
  different MACs but continuous seq_nums are the same device. See
  `client_fingerprints.json:fp-seq-num-continuity`.
- **GAS/ANQP fingerprint.** Passpoint-capable clients emit specific
  ANQP queries; the query set fingerprints the OS.

## Per-OS randomization schedules

| OS               | Scheme                       | Rotation                                       |
| ---              | ---                          | ---                                            |
| iOS 14–17        | Per-SSID persistent          | Same MAC on that SSID forever                  |
| iOS 18+          | Per-SSID + daily rotation    | Fresh MAC each day (still per-SSID)            |
| Android 10–11    | Per-SSID by default          | opt-out per profile                            |
| Android 12+      | Per-SSID persistent          | vendor overrides (Samsung Knox) rotate faster  |
| Windows 10 1809+ | Per-SSID + random-per-connect toggle | opt-in via GPO                          |
| Windows 11       | Per-SSID default             | daily rotation opt-in                          |
| macOS Sonoma+    | Per-SSID                     | previously fixed burned MAC                    |

**LAA bit signature.** Every randomized MAC has the LAA
(Locally-Administered Address) bit set — bit 1 of the first octet.
Second-nibble pattern:

- `x2:xx:xx:xx:xx:xx`
- `x6:xx:xx:xx:xx:xx`
- `xA:xx:xx:xx:xx:xx`
- `xE:xx:xx:xx:xx:xx`

Anything else is a real (burned-in) IEEE-assigned OUI. Filter with
`wlan.sa[0] & 0x02 == 0x02`.

## Per-OS client behavior tables

### EAP-TLS certificate validation defaults

| OS                          | Cert validation default   | Notes                                                                    |
| ---                         | ---                       | ---                                                                      |
| Windows 10 1809+            | GPO-driven                | Domain-joined enforces validation via GPO; non-domain accepts any        |
| Windows 11                  | Same as 10 1809+          | Additional Zero-Trust profile options for organizations                  |
| iOS 12+ / macOS Mojave+     | Enforced + SAN mandate    | Reject certs without SubjectAltName (breaks pre-SAN legacy)              |
| Android 8 (O)               | Optional prompt           | User can accept unknown cert                                             |
| Android 10                  | Default reject on unknown | But allow via explicit trust dialog                                      |
| Android 12+                 | Enforced + SAN mandate    | Modern Android matches iOS behavior                                      |

### Captive-portal detection endpoints

| OS                        | Probe endpoint                                          | Match criterion                        |
| ---                       | ---                                                     | ---                                    |
| iOS / macOS               | `http://captive.apple.com/hotspot-detect.html`          | Body must equal "Success"              |
| Windows 10/11             | `http://www.msftconnecttest.com/connecttest.txt`        | Body must equal "Microsoft Connect Test" |
| Android 5–10              | `http://connectivitycheck.gstatic.com/generate_204`     | HTTP 204                               |
| Android 11+               | `http://connectivitycheck.gstatic.com/generate_204`     | HTTP 204 auto-satisfies, silent dismiss |
| Firefox                   | `http://detectportal.firefox.com/success.txt`           | Body must equal "success"              |
| ChromeOS                  | `http://www.gstatic.com/generate_204`                   | HTTP 204                               |

### Autoconnect refuse rules (posture downgrade)

Modern clients refuse to autoconnect to a known SSID if the security
posture has "downgraded":

- **iOS 16+ / macOS Sonoma+** — refuse to autoconnect if the network
  was originally WPA2/3 but the beacon now advertises Open.
- **Windows 10 21H1+** — same, plus posture-warn on WPA3 → WPA2.
- **Android 12+** — refuse silently; UI shows the network but
  won't join.
- **iOS 17+ / Android 14+** — refuse if the network was seen with PMF
  and PMF is now absent from the beacon.

Consolidated with `records/client_fingerprints.json` +
`records/roaming.json`.

## Correlating across randomized MACs

The strong-signal combination is (Vendor-IE + Extended-Cap bits +
probe-IE order + seq-num continuity). Two frames matching on 3 of 4
axes are almost certainly the same device even under different MACs.

## Records

Backed by `records/client_fingerprints.json`.

## Cite

- IEEE Std 802.11-2020, §9.4 (frames), §11.3 (probe procedure).
- Community fingerprint DBs — Wireshark IEEE OUI, hoover-style probe
  DBs.
