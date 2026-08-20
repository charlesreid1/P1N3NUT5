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
2. **SSID Confusion.** Doesn't need to deauth the target at all.
   See `knowledge/ssid-confusion/walkthrough.md`.
3. **Kr00k on vulnerable clients.** The disassoc trigger still
   applies at the *client's* firmware level; PMF-required at the
   AP does not save a Kr00k-vulnerable client if the attacker can
   spoof a disassoc directly to the client.
4. **BTM-forced roam.** Some vendors' BTM Action-frame handling
   does not require PMF authentication. Craft a BTM Request with
   `hostapd_cli bss_tm_req`; the client cooperates in its own
   move to your rogue.
5. **Rogue-RADIUS / cert-phish.** No deauth needed if the client
   is not associated yet, or if it's willing to associate to a
   stronger-signal rogue.
6. **Multi-Channel MitM.** Dual-radio interposition still works;
   the deauth is not part of the primitive.

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

- IEEE Std 802.11-2020 §11.34 (PMF).
- attacks.json: `deauth-broadcast`, `deauth-targeted`,
  `ssid-confusion-cve-2023-52424`,
  `kr00k-broadcom-cve-2019-15126`, `btm-forced-roam`.
- verify_claim: "PMF prevents all deauth" → needs_qualification.
