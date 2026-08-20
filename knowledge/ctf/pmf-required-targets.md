# PMF-required targets — when deauth is off the table

## Recognition

Beacon RSN Capabilities:
- Bit 6 MFPR (Management Frame Protection Required) = 1
- Bit 7 MFPC (Management Frame Protection Capable) = 1

Both set = PMF is required. Broadcast deauth / disassoc from an
unassociated attacker will not disturb this AP or its clients.

## What still works

1. **Passive capture.** Wait. Reassociations happen naturally.
   The 4-way handshake is not itself PMF-protected, and the M1
   PMKID is not either. `capture_pmkid` still works. Wait for a
   natural reassoc for a full 4-way.
2. **SSID Confusion (CVE-2023-52424).** Doesn't need to deauth
   the target at all. The client's own auto-reconnect logic is
   redirected onto a same-PSK sibling SSID. See
   `knowledge/ssid-confusion/walkthrough.md`.
3. **Kr00k on vulnerable clients (CVE-2019-15126,
   CVE-2020-3702).** The disassoc trigger still applies at the
   *client's* firmware level; PMF-required at the AP does not
   save a Kr00k-vulnerable client if the attacker can spoof a
   disassoc directly to the client. Even without spoofing, a
   *natural* disassoc leaks the tail-frame queue encrypted with
   a zero PTK.
4. **BTM-forced roam.** Some vendors' BTM Action-frame handling
   does not require PMF authentication. Craft a BTM Request with
   `hostapd_cli bss_tm_req`; the client cooperates in its own
   move to your rogue.
5. **Rogue-RADIUS / cert-phish.** No deauth needed if the client
   is not associated yet, or if it's willing to associate to a
   stronger-signal rogue. Karma-family (probe-response attraction)
   also works — PMF applies after association, not before.
6. **Multi-Channel MitM (Vanhoef 2018).** Dual-radio interposition
   still works; the deauth is not part of the primitive. PMF only
   protects mgmt frames, not the multi-channel data-frame trick.
7. **SA Query race (§11.3.5.4).** An unprotected disassoc still
   triggers a 1 s SA Query window at the STA. A spoofed SA Query
   Response times the STA out legitimately. Narrow but real.
8. **FT reassoc capture (802.11r).** FT reassoc frames are
   PMF-protected in transit but the FT key material (PMK-R1
   distribution + reassoc IEs) still yields a hashcat-22000
   hash on capture. Offline crack, no live deauth needed.
9. **Framing Frames (CVE-2022-47522).** Power-save queue-poisoning
   via unprotected TIM / PS-Poll control frames. PMF protects
   mgmt, not control.
10. **Control-frame DoS.** CTS-to-self NAV silencing, RTS/CTS
    abuse, and mdk4 `p` probe flood all target Control frames or
    pre-association mgmt frames — unaffected by PMF. See
    `dos/walkthrough.md` §"What still works when PMF-required".

## What definitely does not work

- `aireplay-ng -0` (broadcast deauth). The AP ignores it, PMF-
  capable clients ignore it. You'll waste airtime.
- Unicast deauth against a PMF-negotiated client. It's
  authenticated with the pairwise key; you don't have the key.

## The MCP behavior

`do_deauth(bssid=…, respect_pmf=True)` (the default) will refuse
to fire against a PMF-required target and return an envelope with
`ok=False` and a citation to `std-802-11w`. The refusal message
includes the correct alternative.

## Cite

- IEEE Std 802.11-2020 §11.34 (PMF), §11.3.5.4 (SA Query),
  §11.10 (BSS Transition).
- Wi-Fi Alliance WPA3 spec — 6 GHz mandatory PMF.
- Vanhoef 2018 (MC-MitM); Gollier & Vanhoef 2024 (SSID Confusion);
  ESET 2019 (Kr00k); Vanhoef 2022 (Framing Frames).
- attacks.json: `deauth-broadcast`, `deauth-targeted`,
  `ssid-confusion-cve-2023-52424`,
  `kr00k-broadcom-cve-2019-15126`, `btm-forced-roam`,
  `sa-query-race`, `framing-frames-cve-2022-47522`,
  `mc-mitm-vanhoef-2018`.
- verify_claim: "PMF prevents all deauth" → needs_qualification.
