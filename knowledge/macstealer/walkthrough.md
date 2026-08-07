# MacStealer walkthrough (short)

1. Join the target network (you have the PSK).
2. Passively observe traffic to identify the victim MAC.
3. Wait for the victim to disconnect (or force it — deauth if PMF is
   off).
4. Spoof the victim's MAC on your interface (`ip link set wlan0 down;
   ip link set wlan0 address <VICTIM_MAC>; ip link set wlan0 up`) and
   associate.
5. Server-side sessions keyed on MAC (rare but non-zero) may deliver
   the victim's next response to you.

Mostly a companion primitive to SSID Confusion / Framing Frames in
practice. In a WCTF the flag surface is usually a session token
returned to the victim MAC that you hijack.

## Cite

- Vanhoef 2023 — MacStealer.
- attacks.json: `macstealer-mac-hijack`.
