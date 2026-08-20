# Framing Frames — power-save queue poisoning

Vanhoef 2023, USENIX Security. The 802.11 power-save state machine
lets a client tell the AP "I'm sleeping — hold my frames." The AP
queues traffic and delivers it when the client wakes (typically at
DTIM intervals). The bug: the AP's queueing does not consistently
tie a queued frame's encryption context to the identity of the
sender who caused it to be queued. An attacker who can spoof frames
on behalf of a sleeping victim can poison that queue and get their
own frames delivered to the victim on wake.

## The primitive

1. Attacker forces the victim into deep sleep by asserting the PM
   bit in a null-data frame from the victim's MAC.
2. Attacker sends frames destined *to* the victim from the LAN side
   (or spoofs a legitimate sender), causing the AP to queue them.
3. Attacker mixes their own crafted frames into the queue with the
   same destination MAC and a manipulated encryption context.
4. Victim wakes; AP flushes the queue; attacker's frames land in
   the victim's stack with client-isolation bypassed.

Details differ by AP firmware; the paper enumerates the classes of
implementations that mishandle the queue-context binding.

## Why it matters

Bypasses client-isolation on many enterprise APs — the setting an
admin turns on specifically to keep guest STAs from talking to each
other.

## Cite

- Vanhoef 2023 — Framing Frames, USENIX Security.
- CVE-2022-47522 — Framing Frames power-save queue tap.
- IEEE Std 802.11-2020 §11.2 (Power management).
- attacks.json: `framing-frames-power-save-poison`.
