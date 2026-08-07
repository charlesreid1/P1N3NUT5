# Framing Frames recognition

Signs a client-isolation-enabled AP is still vulnerable to the
Vanhoef 2023 power-save queue attacks.

## What isolation is *supposed* to prevent

Consumer + enterprise APs offer "client isolation" / "AP isolation" /
"guest isolation" — a config that blocks intra-BSS forwarding so
associated STAs can't talk to each other. This is the property
Framing Frames breaks: an attacker can inject frames destined for a
sleeping victim by manipulating the AP's power-save queue, and the
frames arrive at the victim on wake — bypassing the isolation
control the AP thinks it's enforcing.

## Vulnerable AP fingerprint

Isolation is a per-vendor implementation, and vulnerability status
is per-firmware. Categories:

- **Cheap/consumer APs (TP-Link, D-Link, Netgear "guest" mode).**
  Nearly always vulnerable through at least 2024 firmware. Isolation
  is enforced at the bridging layer, but the power-save queue isn't
  scoped to the isolation rule.
- **OpenWRT stock hostapd.** Vulnerable pre-2.11 hostapd release.
  Patch: `ap_isolate` combined with a power-save queue segregation
  fix landed in hostapd 2.11.
- **Cisco (Aironet / Catalyst 9800).** Patched in IOS-XE 17.9+ per
  Cisco's advisory. Older TrustSec-only isolation is bypassed.
- **Aruba (Instant / ArubaOS-10).** Patched in ArubaOS 10.4+.
- **Ruckus SmartZone / R650/R750 access points.** Patched in
  SmartZone 6.1+.
- **Meraki cloud APs.** Auto-patched via cloud rollout; the exposure
  window closed for most tenants in 2023–2024.

Recon-time way to guess without probing:

- Beacon `Vendor-Specific IE` OUI + subtype → vendor + product line.
- Cross-reference `ap-fingerprinting/reference.md` and
  `chipsets/reference.md`.
- If the vendor's advisory says "patched in FW X" and your beacon-side
  fingerprint suggests FW < X, plausibly vulnerable.

## Client-side preconditions

The attack targets a *sleeping* victim. It needs:

- **A power-saving client** — laptops on battery, phones, IoT.
  Docked/plugged laptops on Ethernet-bridged setups aren't power-saving.
- **TIM/DTIM signaling from the AP** actually being followed (default
  behavior for anything not force-awake).
- **Absence of MFP on the victim's link** for some variants; the
  attack has protected and unprotected primitives.

## Passive signals

Watching a target BSSID:

- **DTIM count in beacons.** A DTIM period > 1 (2–10 common) means
  the AP is buffering multicast/broadcast between DTIMs — the queue
  the attack targets exists and is active.
- **TIM element in beacon.** Filter `wlan_mgt.tim.bmapctl` in Wireshark;
  the bitmap indicates which associated AIDs have queued frames.
  A vulnerable AP populates this per-STA; the attacker can force it
  to buffer via crafted null-data-with-PM-set frames.
- **Client sending Null-data frames with the PM (Power Management)
  bit toggling.** In a pcap, `wlan.fc.pwrmgt == 1` on a Null data
  from the target STA → the STA just entered doze. That's the
  attack window.

## Distinguishing from a plain isolation bug

An AP with broken isolation forwards frames unconditionally. The
Framing Frames primitive is subtler — it requires manipulating the
queue via PM-bit-set nulls followed by an injected frame from the
attacker's side. If the AP is broken enough to forward frames outright,
you don't need Framing Frames.

## The CTF pattern

- Recon shows a target client that goes to sleep predictably (a
  battery-powered IoT device, or a laptop with aggressive power save).
- Recon shows an AP whose fingerprint suggests unpatched firmware.
- The flag is what the client sends *on wake*, injected via the
  poisoned queue — often a token requested from a fake gateway the
  attacker inserts into the STA's frame stream.

## Cite

- Vanhoef 2023 — Framing Frames, USENIX Security 2023.
- knowledge/framing-frames/reference.md.
- attacks.json: `framing-frames-power-save-poison`.
