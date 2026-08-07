# Wi-Fi 6 / 6E — 802.11ax

## What is new

- **OFDMA** — Orthogonal Frequency-Division Multiple Access. Each
  20/40/80/160 MHz channel is subdivided into Resource Units (RUs)
  that the AP allocates to different STAs simultaneously.
- **MU-MIMO uplink** (WPA2/3-Personal added it too, but 6 GHz makes it
  mandatory for CERTIFIED 6E gear).
- **TWT (Target Wake Time)** — client and AP negotiate a schedule of
  when the client can sleep vs. wake. Extends battery life; attackers
  can force clients into extended sleep by injecting spoofed TWT
  action frames.
- **BSS Coloring** — 6-bit color per BSS reduces spatial reuse
  interference. Not directly attack-relevant.
- **Trigger frames** — AP-emitted frames that instruct STAs to send
  in a coordinated uplink OFDMA transmission.
- **HE Capabilities / HE Operation IEs** — the new advertisement
  elements. IE 255 with extension IDs 35 (HE Capabilities) and 36
  (HE Operation).
- **Reduced Neighbor Report (RNR, IE 201)** — 6 GHz APs advertise
  themselves via RNR IEs in *2.4/5 GHz* beacons. Big recon lever:
  you can enumerate 6 GHz targets from a card that cannot tune 6 GHz.

## 6 GHz specifics (Wi-Fi 6E)

- US: channels 1..233, UNII-5 / -6 / -7 / -8.
- **WPA3-only mandate.** No transition mode; WPA2 clients cannot
  associate on 6 GHz.
- Regulatory: LPI (Low Power Indoor), SP (Standard Power via AFC),
  and VLP (Very Low Power) tiers.

## Attack surfaces

- **TWT forced-sleep** — inject a spoofed TWT Setup frame with a long
  wake interval; the client stops receiving. Companion to Framing
  Frames. See `attacks.json:twt-forced-sleep-abuse`.
- **RNR-driven 6 GHz recon** — scan 2.4/5 GHz beacons, parse RNR IEs,
  enumerate 6 GHz BSSIDs without a 6 GHz radio. See
  `attacks.json:rnr-6ghz-enumeration`.
- **RU-based OFDMA DoS** — request allocations for RUs you never
  transmit on, or flood with malformed trigger responses.
- **6 GHz reduces to Dragonblood-family reasoning.** Since WPA3-SAE is
  the only game in 6 GHz, every attack on 6 GHz auth is really a WPA3
  attack — Dragonblood side-channel or transition-mode downgrade
  (which does NOT apply on 6 GHz because transition mode is forbidden
  there).

## Cite

- IEEE Std 802.11ax-2021.
- Wi-Fi Alliance — Wi-Fi CERTIFIED 6E requirements.
- attacks.json: `twt-forced-sleep-abuse`, `rnr-6ghz-enumeration`,
  `ru-based-ofdma-dos`.
