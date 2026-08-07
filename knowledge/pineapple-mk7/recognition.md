# Pineapple Mk VII — is it in a good state?

A pre-engagement checklist. Run before the CTF starts. Every check
maps to a symptom the Pineapple exhibits mid-engagement when it's
been misconfigured, and each has a direct fix from either the MCP
tool surface or SSH.

## 1. It's reachable

```
ping -c 3 172.16.42.1                 # or your $PINEAPPLE_HOST
```

- No response → USB tether not up. Reseat USB-C, check host's
  network interface came up (`ifconfig` on macOS, `ip link` on
  Linux).
- Response but slow → power-hungry radios pulled voltage; use a
  powered USB hub or a USB-C laptop that delivers 5V/2A.

## 2. WebUI + API answer

```
curl -sk https://172.16.42.1:1471/api/dashboard \
  -H "Authorization: Bearer $PINEAPPLE_TOKEN" | jq .
```

- 401 → wrong or expired token. Re-issue from WebUI Admin.
- 404 → wrong port or the WebUI's not running. `ssh` in and check
  `service pineapd status`.
- HTTPS handshake fails → firmware upgraded and the self-signed cert
  rotated; refresh your local trust or use `-k`.

Via the MCP: `pineapple_status()` — returns firmware version, uptime,
radio inventory.

## 3. SSH is up and keyed

```
ssh -i "$PINEAPPLE_SSH_KEY" root@172.16.42.1 uname -a
```

- Prompted for password → key not installed. Append to
  `/etc/dropbear/authorized_keys` via one-time password login.
- Connection closed by remote → dropbear crashed or firewall dropped
  it. Reboot: `reboot` via WebUI or unplug/replug.

## 4. Both radios present and in the mode you expect

```
ssh root@172.16.42.1 'iw dev'
```

Expected: `wlan0` and `wlan1`. Typical engagement layout:

- `wlan0` (2.4 GHz, MT7628) — pin to target channel, run hostapd or
  hcxdumptool.
- `wlan1` (2.4/5 GHz, MT7615) — recon + PineAP.

Symptoms:

- Only one wlan shown → a radio didn't come up. Common causes: the
  MT7615 firmware failed to load (`dmesg` will show it), or a
  previous session left the radio down (`iw dev wlan1 set type
  managed && ip link set wlan1 up`).
- Both shown but `type IBSS` or `type monitor` on the wrong one →
  leftover state. Reset: `service pineapd restart` or reboot.

## 5. PineAP is off (unless you meant it on)

Recon that runs alongside a live PineAP karma session will pollute
the AP list with your own beacons. Confirm:

```
curl -sk https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" | jq .karma
```

Expected `0` at engagement start. If `1` and you didn't want it on,
disable via `pineap_stop()` or:

```
curl -sk -X POST https://172.16.42.1:1471/api/pineap/settings \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"karma": 0, "broadcast_ssid_pool": 0, "beacon_response": 0}'
```

## 6. Filter lists are clear (or intentionally populated)

Leftover SSID / MAC allow/deny lists from a previous run silently
change what recon reports and what PineAP responds to.

```
curl -sk https://172.16.42.1:1471/api/pineap/filter/ssids \
  -H "Authorization: Bearer $TOKEN" | jq .
curl -sk https://172.16.42.1:1471/api/pineap/filter/clients \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Clear if the config isn't for this engagement.

## 7. Captures dir isn't full

```
ssh root@172.16.42.1 'df -h /root/captures'
```

Under 60% used → fine. Over 80% → move captures to laptop or an SD
card and clean up.

## 8. Time is correct

The Mark VII doesn't have an RTC that survives a full power cycle.
NTP sync happens once online. If time is wildly off, TLS handshakes
(WebUI, some captive-portal upstream fetches) fail.

```
ssh root@172.16.42.1 'date; hwclock 2>/dev/null'
```

Fix: `ntpd -q -p pool.ntp.org` if the device has internet, or
`date -s '2026-08-06 09:00:00'` for a manual set.

## 9. Firmware version matches your `pineapple_endpoints.json` pins

The API path shapes drift across firmware. Each endpoint record
carries `firmware_min` and `firmware_max`. If your Pineapple is on
firmware older than the record's minimum, that MCP tool will fail
in surprising ways.

```
pineapple_status()  # returns firmware version
```

Cross-reference against `pineapple_endpoints.json`. If drifted, either
upgrade the Pineapple or narrow the tool set you'll use.

## 10. LEDs

Front-panel LEDs tell you a story at a glance:

- Power LED off → not receiving power.
- System LED not slow-pulsing → not fully booted; wait 60s from
  power-on.
- WiFi LEDs solid on both bands → radios are up.
- Any LED blinking rapidly with no scripted attack running → PineAP
  or another module is transmitting; not neutral.

## 11. The MCP itself works

From the laptop:

```
p1n3nut5-mcp --check
```

Should print: reachable, firmware, radios, PineAP state, filter
count, capture-dir usage, time-skew. This wraps checks 1–8 above
and is the pre-flight the assistant should run at session start.

## When to factory-reset

Never during a CTF unless you've exhausted other paths. Reset button
held 10s during power-on → firmware reload; captures on SD survive;
internal state (SSH keys, WebUI token, PineAP config, filter lists)
wipes. See `pineapple-mk7/reference.md § Factory reset` for the
button location and post-reset re-provisioning steps.

## Cite

- Hak5 WiFi Pineapple Mark VII documentation.
- knowledge/pineapple-mk7/reference.md.
- knowledge/pineapple-mk7/walkthrough.md.
- knowledge/records/pineapple_endpoints.json.
