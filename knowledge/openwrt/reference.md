# OpenWRT — the userland underneath the Pineapple

Everything on the Mark VII is OpenWRT plus a Hak5 module stack.
Everything below runs over SSH.

## UCI — the canonical config

```
uci show                 # dump everything
uci show wireless        # just the wireless config
uci set wireless.radio0.channel=6
uci commit wireless
wifi reload              # apply
```

See `records/openwrt_uci.json` for the section catalog with keys.

## The filesystem you touch during an engagement

```
/etc/config/                UCI files (wireless, network, dhcp, firewall)
/tmp/                       runtime state — /tmp/dhcp.leases,
                            /tmp/hostapd*.conf, hcxdumptool captures
/tmp/log/                   logs (persist across reboot on Mark VII)
/root/                      per-op scripts, uploaded configs
/var/log/                   longer-lived logs (per-service)
/etc/pineapple/            first-party Pineapple config
/pineapple/                 module install locations
```

Common recipes:

```
# Dump current AP config
uci export wireless

# Disable a running hostapd instance
wifi down radio1

# Force a specific channel + width
uci set wireless.radio0.channel=44
uci set wireless.radio0.htmode=VHT80
uci commit wireless
wifi reload

# Set the second radio to monitor mode
uci set wireless.@wifi-iface[1].mode=monitor
uci commit wireless
wifi reload
```

## Useful non-UCI daemons

- `hostapd` — see `hostapd/`.
- `wpa_supplicant` — client-side associations from the Pineapple.
- `dnsmasq` — DHCP + DNS; captive-portal work configures it heavily.
- `iw`, `iwconfig` (legacy) — direct kernel netlink to the wireless
  driver.
- `logread -f` — the OpenWRT syslog tail. Look here when hostapd or
  hcxdumptool silently fails.
- `procd` — the init system. `procd_start /etc/init.d/network`.

## Cite

- OpenWRT UCI documentation.
- Hak5 Mark VII documentation.
- knowledge/openwrt_uci.json (record catalog with byte-level detail).
