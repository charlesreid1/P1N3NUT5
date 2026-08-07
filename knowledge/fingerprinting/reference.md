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

- **iOS 14+** — per-SSID. Persistent within one network, fresh per
  network.
- **Android 10+** — per-SSID by default, opt-out per network. Vendor
  overrides (Samsung Knox etc.) vary.
- **Windows 10/11** — per-connection, opt-in per profile.
- **macOS Sonoma+** — per-SSID (previously fixed burned MAC).

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
