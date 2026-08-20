# Deauth recognition

How to spot a deauth attack in a capture — and how a WIDS spots yours.

## In a pcap

Filter `wlan.fc.type_subtype == 12` (deauthentication) or `== 10`
(disassociation). Look at:

- **Frame count over time.** A single legitimate deauth per session
  disassoc is normal. Dozens per second is not.
- **Reason code.** Legit deauths carry `1` (unspecified),
  `3` (leaving BSS), `4` (inactivity). Attack tool defaults —
  version-dependent, check the build:
  - `aireplay-ng -0` — the exact default varies across releases;
    aircrack-ng ≤ 1.6 typically emitted reason `7` ("class 3 frame
    from nonassociated STA"), while 1.7+ defaults to reason `1`.
    Either way, callers usually set an explicit reason with
    `--deauth <code>`; treat "no reason override" as ambiguous
    and let the version identify the fingerprint.
  - `mdk4 d` → reason `1` unless overridden.
  - `hcxdumptool` (6.x+) → does **not** send deauths at all; active
    attack modes were removed in 6.x. If a capture using hcxdumptool
    coincides with deauths, they are coming from a separately-driven
    tool (mdk4, aireplay-ng, scapy) on the same operator's rig.
  Reason `7` in volume (with no cover traffic) is still a strong
  fingerprint of legacy `aireplay -0` on aircrack-ng ≤ 1.6.
- **Address triple.** Broadcast deauth: DA = `FF:FF:FF:FF:FF:FF`,
  BSSID = target AP. Targeted: DA = victim STA, TA/BSSID = AP.
  Attackers spoof TA to look like the AP.
- **Sequence numbers.** A real AP increments monotonically; an
  attacker's injection tool often resets to 0 or skips wildly. A
  seq-num discontinuity between beacons (real AP) and deauths
  (claiming to be from AP) is a giveaway.

## WIDS heuristics you're tripping

- **Rate anomaly.** Any deauth rate >5/sec from a single TA fires an
  alert on Cisco WLC, Aruba, Ruckus, and Ekahau WIDS.
- **Non-associated STA deauths.** Deauthing a MAC the AP has never
  seen associate → the WIDS knows this can't be the AP.
- **Reason code 7 storms.** Every commercial WIDS has "aireplay
  signature" as a preloaded rule.
- **PMF-required BSSID getting unprotected deauths.** A PMF-capable
  AP flags unauthenticated deauths as impossible; the frame is
  malformed by definition.
- **Cross-channel deauth.** An AP on channel 6 doesn't transmit
  frames on channel 11. If your monitor iface sees a deauth "from"
  the AP on a channel the AP isn't on, that's the injecting radio.

## PMF interaction

- **PMF disabled (RSN Capabilities bit 6/7 = 0/0):** all deauth
  works. This is the classic Tier-1 target.
- **PMF optional (1/0):** works against clients that didn't
  negotiate PMF. In a mixed group, unicast the ones you can.
- **PMF required (1/1):** broadcast deauth is silently dropped.
  Unicast requires a valid MIC — you can't forge it. Pivot: Kr00k
  disassoc-and-decrypt on vulnerable clients, SSID Confusion, or
  MC-MitM instead of deauth.

## Distinguishing attacker family from the frame

- Constant reason=7 + tight timing + broadcast DA → legacy
  `aireplay-ng -0` (aircrack-ng ≤ 1.6 default). Newer aircrack-ng
  (1.7+) defaults to reason 1; `--deauth <code>` overrides either.
- Reason=1, bursty timing, seq gaps → `mdk4 d`.
- Reason=1/7 from an aireplay-ng or mdk4 process running alongside
  an `hcxdumptool` channel-locked capture → the PMKID/handshake
  pipeline, since 6.x hcxdumptool itself no longer deauths.
- Reason=3, one-shot per STA, immediately followed by an M1 from
  the same BSSID → someone driving a WPA2 4-way capture.

## Cite

- IEEE Std 802.11-2020, §9.4.1.7 (reason codes), §11.3.5 (deauth).
- knowledge/deauth/reference.md.
- attacks.json: `deauth-broadcast`, `deauth-targeted`,
  `disassoc-targeted`.
