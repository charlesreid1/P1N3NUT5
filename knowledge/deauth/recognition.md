# Deauth recognition

How to spot a deauth attack in a capture — and how a WIDS spots yours.

## In a pcap

Filter `wlan.fc.type_subtype == 12` (deauthentication) or `== 10`
(disassociation). Look at:

- **Frame count over time.** A single legitimate deauth per session
  disassoc is normal. Dozens per second is not.
- **Reason code.** Legit deauths carry `1` (unspecified),
  `3` (leaving BSS), `4` (inactivity). Attack tools default:
  - `aireplay-ng -0` → reason `7` ("class 3 frame from nonassociated STA")
  - `mdk4 d` → reason `1` unless overridden
  - `hcxdumptool` client kick → reason `2`
  Reason `7` in volume is a near-certain fingerprint of an old-school
  `aireplay -0`.
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

- Constant reason=7 + tight timing + broadcast DA → `aireplay-ng -0`.
- Reason=1, bursty timing, seq gaps → `mdk4 d`.
- Reason=2, targeted, coincides with an `hcxdumptool`
  channel-locked capture → PMKID/handshake pipeline.
- Reason=3, one-shot per STA, immediately followed by an M1 from
  the same BSSID → someone driving a WPA2 4-way capture.

## Cite

- IEEE Std 802.11-2020, §9.4.1.7 (reason codes), §11.3.5 (deauth).
- knowledge/deauth/reference.md.
- attacks.json: `deauth-broadcast`, `deauth-targeted`,
  `disassoc-targeted`.
