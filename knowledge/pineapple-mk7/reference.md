# Hak5 WiFi Pineapple Mark VII — hardware + firmware

## Hardware

- **2 radios** — wlan0 (2.4 GHz, MT7628) and wlan1 (2.4/5 GHz, MT7615).
- **1 USB-C** for tether to laptop (`172.16.42.1` by default).
- **1 USB-A** — attach a 3rd external adapter for a big engagement
  (bettercap driving one; hcxdumptool driving another; hostapd on
  a third).
- **8 GB internal flash** for OS + logs + captured pcaps.
- **Optional SD card** for capture storage (recommended).
- **4 LEDs** — power / system / WiFi 2.4 / WiFi 5. Blinky patterns
  are documented in the vendor manual.

## Two radios, two roles

The Pineapple's engineering trick: run recon and attack simultaneously
on separate radios. Typical division of labor:

- **wlan0 (2.4 GHz only)** — pin to the target AP's channel; run
  hostapd or hcxdumptool.
- **wlan1 (2.4/5 GHz)** — passive recon + PineAP karma.

For MC-MitM (see `mc-mitm/`) the two radios interpose on different
channels simultaneously.

## The WebUI + API

- Bearer-token authentication (from the Admin page).
- Default URL: `https://172.16.42.1:1471/` (varies by firmware).
- REST paths under `/api/*` — see `pineapple_endpoints.json`.

## Storage

Captures land under `/root/captures/` by default. On busy days you
will fill 8 GB fast; move to SD or scp back to the laptop mid-run.

## Fresh-setup checklist

1. Power up over USB-C to a laptop.
2. `ssh root@172.16.42.1` — first-boot password prompt.
3. Change password. Add your SSH key to `/etc/dropbear/authorized_keys`.
4. Log into WebUI `https://172.16.42.1:1471`. Note the API token.
5. Set `PINEAPPLE_HOST`, `PINEAPPLE_TOKEN`, `PINEAPPLE_SSH_KEY` in
   your shell env (see `plan-organize.md § Env vars`).
6. Test: `p1n3nut5-mcp` (starts the MCP) and call `pineapple_status()`.

## Factory reset from a wedged state

Hold the reset button for 10s while power is applied. Firmware
reloads from an internal image. Any SD-card captures survive; internal
flash is wiped.

## Cite

- Hak5 Mark VII documentation.
- knowledge/pineapple_endpoints.json (record catalog for every path).
