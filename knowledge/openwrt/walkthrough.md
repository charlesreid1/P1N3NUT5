# OpenWRT — walkthrough

Everything on the Pineapple Mk VII runs OpenWRT. Every attack that
needs a rogue AP, a fresh iface, or a UCI tweak lives here. This is
the operational playbook — see `records/openwrt_uci.json` for the
full section catalog.

## Preconditions

- Root SSH to the Pineapple (`ssh root@172.16.42.1`, default port 22).
- Familiarity with `uci`, `wifi`, `iw` command shapes.

## Path A — Show current wireless config

```
# Everything wireless
uci show wireless

# Just the interfaces
uci show wireless | grep '^wireless\.@wifi-iface'
```

Each interface has:

- `device` — physical radio (radio0 = wlan0, radio1 = wlan1).
- `network` — the L2 network it belongs to (lan / wan / rogue).
- `mode` — ap / sta / monitor / mesh.
- `ssid`, `encryption`, `key` — obvious.

## Path B — Bring wlan1 into monitor mode via UCI

```
uci set wireless.@wifi-iface[1].mode=monitor
uci set wireless.@wifi-iface[1].ssid=""
uci commit wireless
wifi reload
iw dev
# Look for wlan1 with type monitor.
```

Or bypass UCI entirely with `iw`:

```
ip link set wlan1 down
iw dev wlan1 set type monitor
ip link set wlan1 up
```

The `iw` path is faster; UCI change persists across reboots.

## Path C — Stand up a rogue AP interface via UCI

```
# Add a new wifi-iface on radio1 (wlan1).
uci add wireless wifi-iface
uci set wireless.@wifi-iface[-1].device=radio1
uci set wireless.@wifi-iface[-1].network=lan
uci set wireless.@wifi-iface[-1].mode=ap
uci set wireless.@wifi-iface[-1].ssid=EvilTwin
uci set wireless.@wifi-iface[-1].encryption=none
uci commit wireless
wifi reload
```

## Path D — Add a rogue WPA2-PSK network

```
uci add wireless wifi-iface
uci set wireless.@wifi-iface[-1].device=radio1
uci set wireless.@wifi-iface[-1].mode=ap
uci set wireless.@wifi-iface[-1].ssid=CorpWiFi
uci set wireless.@wifi-iface[-1].encryption=psk2
uci set wireless.@wifi-iface[-1].key='<known-PSK>'
uci commit wireless
wifi reload
```

## Path E — Channel / power

```
# Set channel on radio0 (2.4 GHz):
uci set wireless.radio0.channel=6
uci set wireless.radio0.hwmode=11g
uci set wireless.radio0.txpower=20     # dBm
uci commit wireless
wifi reload
```

## Path F — Firewall rules for isolated engagement

Prevent the Pineapple from leaking traffic to the WCTF's real
network via the WAN uplink:

```
# Kill routing from the rogue network to WAN
uci add firewall rule
uci set firewall.@rule[-1].src=lan
uci set firewall.@rule[-1].dest=wan
uci set firewall.@rule[-1].target=REJECT
uci commit firewall
/etc/init.d/firewall restart
```

## Path G — Common recipes

### Dump wireless config

```
uci show wireless
iw dev
iw phy
```

### Disable a running service

```
/etc/init.d/hostapd stop
/etc/init.d/hostapd disable
```

### Force a channel outside regdomain (careful)

```
iw reg set BO      # bolivia regdomain — high TX limits
```

Regulatory-questionable; at a con floor this creates interference
that's on you.

### Monitor mode on a driver that resists

Some ath10k builds resist monitor mode:

```
echo "options ath10k_core rawmode=1" > /etc/modules.d/ath10k.conf
reboot
```

## Path H — Reading system logs

```
logread                # all recent
logread -f             # follow
logread -e hostapd     # filter to hostapd
logread -e wpa         # any wpa_* daemon
```

## Failure modes

- **`uci commit` succeeds but `wifi reload` doesn't apply.**
  UCI commit only writes to `/etc/config/`; a second daemon may be
  overriding. Check `/etc/init.d/` scripts.
- **`iw dev wlan1 set type monitor` fails.** Interface up. `ip link
  set wlan1 down` first.
- **Package install fails on opkg.** `opkg update` first; the Mk VII
  ships a very small repo list. Some packages need adding the OpenWRT
  main repo (regulatory- and version-specific).
- **Config wipe on firmware update.** Pineapple firmware updates
  reset UCI to defaults. Back up `/etc/config/*` before flashing.

## Cite

- OpenWRT UCI documentation.
- Hak5 Mark VII documentation.
- `records/openwrt_uci.json` — section catalog.
