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
identity* that survives disconnect.

The specific AP-side state that makes this work: **the AP maintains
one TX queue per STA MAC.** On some implementations, when a STA
disassociates the queue is NOT flushed — the AP simply keeps holding
frames that were destined for the disassoc'd MAC, waiting to redeliver
them when the STA returns. When a *new* STA associates with the same
MAC (spoofed by the attacker) and completes its own 4-way handshake,
the queued frames get released encrypted under the attacker's fresh
PTK. The AP does the decryption/re-encryption work for you.

Concretely, when the victim disassociates and the attacker (already on
the network) reassociates under the victim's MAC:

1. Attacker waits for (or forces) the victim's disassociation. Buggy AP
   leaves the per-STA TX queue populated with un-delivered downlink
   frames.
2. Attacker associates its own radio using the victim's MAC and
   completes a fresh 4-way handshake — new PTK derived from the
   attacker's ANonce/SNonce, but bound only to the borrowed MAC as
   "session identity."
3. AP dequeues the buffered frames and encrypts them under the
   attacker's new PTK. Attacker decrypts them locally.

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
