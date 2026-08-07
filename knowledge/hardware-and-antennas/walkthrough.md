# hardware-and-antennas — walkthrough

Choosing, mounting, aiming, and validating.

## Path A — Con-floor engagement (2026 DEF CON)

**Threat model**: 200 APs, 3000 STAs, everyone within 40 m. RSSI
dominates over range.

- Antennas: dual 9 dBi omnis or a 60° panel oriented at the target's
  general direction.
- Adapter: Alfa AWUS036ACM (mt76) for supplemental capture; the
  Pineapple's built-in radios for the rogue AP.
- Cable: as short as possible. Every meter of RG-58 loses ~0.7 dB
  at 5 GHz.

## Path B — Bench engagement (single target)

**Threat model**: one target device, 10 m away, quiet room.

- Antennas: 12 dBi panel aimed carefully.
- Adapter: whichever has best monitor+injection on the target band.
- Position: line-of-sight, elevated slightly above the target.

## Path C — Extreme range (WCTF puzzle across a hallway)

**Threat model**: target AP 50–100 m away.

- Antennas: 15–18 dBi yagi or biquad, hand-aimed.
- Adapter: Alfa AWUS036ACH or AXML with the yagi bolted directly
  onto the SMA (no cable if possible).
- Consider driving the antenna from a laptop closer to the target
  and SSHing back — RF > USB in this scenario.

## Path D — Setting TX power (respect + reality)

```
# See what your regdomain allows.
iw reg get

# Set regdomain (some drivers reset TX cap accordingly).
iw reg set US

# Attempt to set TX power (may silently cap to regdomain limit).
iw dev wlan1 set txpower fixed 3000     # 30 dBm

# Verify what actually got applied.
iw dev wlan1 info
```

Some drivers (ath9k especially) let you exceed the regdomain cap if
you set the domain to `BO` (Bolivia — high cap regdomain used as a
loophole). This is regulatory-illegal in most jurisdictions; at a
con floor with 200 attackers on the same channel, it also creates
a nuisance-interference problem.

## Path E — Validating an adapter's monitor + injection

```
# Bring the adapter into monitor mode.
sudo airmon-ng start wlan1
# (or: iw dev wlan1 set type monitor && ip link set wlan1 up)

# Test injection.
sudo aireplay-ng --test wlan1mon
# Expected: "Injection is working!" and 30/30 packets received.

# If injection is <100%:
#   - RSSI too low — get closer or use a better antenna.
#   - Driver only supports monitor, not injection (Intel iwlwifi).
#   - You're on a DFS channel and the driver is silent-avoiding.
```

## Path F — Aiming a directional antenna

```
# Bring up a monitor iface.
sudo airmon-ng start wlan1

# Watch target RSSI in real time.
airodump-ng --band abg --essid CorpWiFi wlan1mon
```

Rotate the antenna slowly; watch the RSSI column. Peak the number.
A well-aimed yagi at 5 GHz has a ~30° 3 dB beamwidth — small
adjustments matter. Peak on the *client* MAC, not the AP, if you're
attacking the client side.

## Path G — Diagnosing "adapter isn't working"

Order of checks:

1. `lsusb` — is the adapter enumerated?
2. `dmesg | tail -50` — did the driver bind?
3. `iw dev` — is the interface listed?
4. `rfkill list` — is soft-blocked?
5. `iw reg get` — is regdomain set (some drivers refuse until it is)?
6. `airmon-ng check` — is NetworkManager or wpa_supplicant fighting?

Common fix: `airmon-ng check kill` to kill NetworkManager,
wpa_supplicant, and dhclient before monitor-mode work.

## Failure modes

- **Adapter shows in `lsusb` but not `iw dev`.** Driver not loaded.
  Check `dmesg`. Some adapters (RTL8812BU) need `rtl88x2bu-dkms` on
  older kernels.
- **Monitor works but injection doesn't.** Intel iwlwifi does this
  by design. Use a different card.
- **DFS channel silence.** Some drivers stop transmitting on
  DFS-required channels until they see the AP's beacon; not a bug,
  a regulatory feature. Use UNII-1 or UNII-3 instead if possible.
- **6 GHz card refuses to tune 6 GHz.** Even 6E-capable cards need
  a regdomain that allows 6 GHz + a firmware that supports it in
  monitor mode. Support was thin as of 2024, better by 2026 but
  still adapter-specific.

## Cite

- Alfa Network, Panda Wireless, TP-Link datasheets.
- linux-wireless driver matrix (kernel.org).
- aircrack-ng documentation.
- FCC Part 15, ETSI EN 300 328 / 301 893.
