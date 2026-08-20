# MacStealer — MAC-based traffic hijack

Vanhoef, BlackHat Asia 2023. Client-side flaw in the way 802.11 stacks
handle the association state that carries traffic back to a specific MAC.
When a client disconnects (deauth / disassoc / clean unassociate) and later
reconnects to the same network, some AP + client implementations continue
to accept frames destined for the client's *previous* MAC identity — from
any station that supplies the right MAC in Address 1. An attacker who is
on the network (has the PSK, or the network is Open / OWE) and knows the
victim's MAC can hijack the victim's return traffic.

Filed under CVE-2022-47521 (Linux mac80211 mishandling) with the
sibling power-save-queue tap tracked as CVE-2022-47522 (Framing Frames);
the paper documents the primitive as a class that affects multiple
implementations. Vendor-side fixes rolled out piecewise across
2023–2024; the client-side residual is what still lands in 2026.

## Primitive at the byte level

The 802.11-2020 §12 data-plane binds encryption to a **pairwise session
keyed off the PMK, the ANonce, the SNonce, and both MAC addresses** —
the client MAC and the AP MAC. What it does not bind is a *session
identity* that survives disconnect. When the victim disassociates and the
attacker (already associated to the AP) sends the AP a QoS Data frame
with Address 1 = attacker MAC + Address 3 = target-server MAC and later
reassociates *itself* under the victim's MAC:

1. Attacker requests a MAC change of its own STA to victim's MAC before
   the AP has cleared the victim's association state.
2. Attacker completes its own 4-way handshake under the borrowed MAC.
3. AP now routes any pending return traffic that was addressed to the
   victim MAC through the attacker's session.

The failure mode is at the AP: it treats the MAC as the session identity
instead of the crypto binding of the 4-way. On patched APs the bind is
tighter — the association state is keyed on (MAC, ANonce) so a
reassociation drops any queued frames destined for the previous session.

## Composition with related attacks

- **SSID Confusion (CVE-2023-52424)** — the two attacks share the client-
  side trust-on-SSID theme. MacStealer requires the attacker to be a
  legitimate STA on the network; SSID Confusion is used *earlier* to get
  the attacker there without a real PSK.
- **Framing Frames (Vanhoef 2023)** — the sibling paper. Framing Frames
  abuses the AP-side power-save queue; MacStealer abuses the AP-side
  post-disconnect queue. Both are AP-side state-machine flaws that fail
  to bind the client's session identity to the crypto session.
- **Client isolation** as a defense: naive implementations MAC-key the
  isolation rules and fail; correct implementations bind isolation to the
  4-way session and hold.

## Affected implementations (2026)

Vanhoef's original paper covered Linux kernel Wi-Fi stack (mac80211),
FreeBSD, and several commercial AP vendors. As of mid-2026:

- **Patched:** Linux mac80211 6.1+ (backport patches issued 2023-Q3),
  hostapd 2.11-devel and later, most enterprise APs (Cisco, Aruba, Ruckus)
  on 2024+ firmware.
- **Still vulnerable:** cheap consumer routers on 2020-era firmware
  without an update path; some IoT bridge devices; residual embedded
  Linux Wi-Fi drivers in industrial gateways.

The client side receives no fix — MacStealer is an AP-side data-plane
flaw. A patched AP fully defends; an unpatched AP with fully-patched
clients is still vulnerable.

## Cite

- Vanhoef, "MacStealer" — BlackHat Asia 2023 slides + paper.
- CVE-2022-47521 (MacStealer / Linux mac80211).
- CVE-2022-47522 (companion Framing Frames power-save queue tap).
- IEEE Std 802.11-2020 §12 (data confidentiality — PTK binding).
- `attacks.json: macstealer-mac-hijack`.
- Companion: `attacks.json: ssid-confusion-cve-2023-52424`,
  `attacks.json: framing-frames-power-save-poison`.
