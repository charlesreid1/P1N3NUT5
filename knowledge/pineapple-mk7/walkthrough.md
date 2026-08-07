# Pineapple Mk VII — walkthrough

Fresh setup → engagement-ready → factory reset from a wedged state.
Everything below assumes the tether cable is connected (default
`172.16.42.1`).

## Path A — Fresh setup

1. Plug in the USB-C tether cable.
2. Wait ~40 s for boot. LEDs pattern: power steady → system blinking
   → both blinking → both steady = ready.
3. Open the WebUI: `https://172.16.42.1:1471/` (self-signed).
4. Default first-time flow prompts for a root password and admin
   password. Set both.
5. SSH test: `ssh root@172.16.42.1` — should accept the root password.

## Path B — Upload your engagement key

```
# On workstation:
ssh-copy-id -i ~/.ssh/pineapple_key.pub root@172.16.42.1
```

Then disable password auth in `/etc/config/dropbear`:

```
uci set dropbear.@dropbear[0].PasswordAuth=off
uci commit dropbear
/etc/init.d/dropbear restart
```

## Path C — First-60-seconds health check

```
# From workstation:
ssh root@172.16.42.1 << 'CHECK'
uname -a                          # firmware kernel
uci get pineap.@config[0].fw     # firmware version
iw dev                            # wlan0 + wlan1 present?
iw reg get                        # regdomain set?
df -h                             # storage remaining
free -m                           # memory
uptime                            # obviously
CHECK
```

- **wlan0** — 2.4 GHz only (MT7628).
- **wlan1** — dual-band (MT7615).
- **Regdomain** — set to US (or your region) for TX-power
  compliance.
- **Storage** — 8 GB internal; big captures fill fast; use SD card.

## Path D — Firmware update

Two paths:

- **WebUI** → Update → Check → Install.
- **CLI**:

```
opkg update
opkg upgrade
# Or download the .bin from Hak5 and flash:
sysupgrade -v /tmp/pineapple_firmware_x.y.z.bin
```

`sysupgrade` preserves `/etc/config/*` by default. `sysupgrade -n`
wipes everything.

## Path E — Factory reset (from WebUI)

Reset → confirm → wait 2 minutes.

## Path F — Factory reset (from a wedged state)

If the WebUI won't load:

1. **Hard-reset button** — hold for 10 seconds while powered.
2. **U-boot recovery** — if the OS won't boot at all:
   - Hold reset while plugging in USB.
   - LED pattern indicates recovery mode.
   - Web UI on `http://172.16.42.1/` (HTTP, not HTTPS) offers
     firmware upload.

## Path G — Multi-radio deployment during engagement

Two Pineapple radios + one external USB-adapter = three simultaneous
capabilities:

- **wlan0 (2.4)** — recon on target channel; passive log.
- **wlan1 (5)** — rogue AP or 5 GHz recon.
- **wlan2 (external USB)** — hcxdumptool aggressive capture on
  another channel.

Wire this up:

```
# Attach the external adapter.
lsusb    # confirm it enumerates.
ip link  # confirm wlan2 shows up.

# Bring it into monitor:
ip link set wlan2 down
iw dev wlan2 set type monitor
ip link set wlan2 up
iw dev wlan2 set channel 11

# Now three radios operating independently.
```

## Path H — Storage layout

- `/root/` — persistent, small. Configs, small scripts.
- `/tmp/` — RAM-backed. Fast but volatile — big captures go here
  during the engagement; move to SD before reboot.
- `/mnt/sd/` (if SD present) — persistent, big captures.

Before reboot:

```
mv /tmp/*.pcapng /mnt/sd/captures/
```

## Path I — LED pattern reference

- **Power (blue)** — solid = on.
- **System (blue)** — blinking = boot; solid = ready.
- **WiFi 2.4 (green)** — blinking = active traffic.
- **WiFi 5 (green)** — same for wlan1.
- **All 4 blinking rapidly for 5 s then solid** — firmware update
  installed successfully.

## Failure modes

- **WebUI unreachable but SSH works.** WebUI daemon crashed. `logread
  -e nginx` or restart `/etc/init.d/pineap`.
- **SSH unreachable but ping works.** `dropbear` failed. Only
  recovery: hard-reset button or U-boot.
- **Ping fails too.** USB-C cable is data-poor. Try a known-good
  cable.
- **Firmware update bricks device.** Very rare; use U-boot recovery
  (Path F).
- **Captures fill /tmp then disk full.** Move to SD card mid-capture:
  `mv /tmp/foo.pcapng /mnt/sd/` — hcxdumptool follows the moved file.

## Cite

- Hak5 WiFi Pineapple Mark VII documentation.
- OpenWRT sysupgrade documentation.
- `records/pineapple_endpoints.json` — full API surface.
