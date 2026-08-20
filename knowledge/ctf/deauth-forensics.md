# Deauth forensics — the flag is in the deauth

**Verified against:** tshark 4.2 as of 2026-Q3

Some WCTF puzzles hand you a pcap of a "deauth storm" and ask what
happened. The flag is either the specific reason code, a signature
in the pattern (timing, sequence, addresses), or an OUI in the
attacker's source MAC.

## Recognition

- Puzzle is a pcap, not a live target.
- Filter shows many deauth/disassoc frames:
  `wlan.fc.type_subtype == 0x0c` (deauth) or `0x0a` (disassoc).
- Distinct patterns: high rate, one attacker MAC, or one victim.

## The analysis sequence

```
# 1. Count deauths by (source, reason).
tshark -r storm.pcapng -Y "wlan.fc.type_subtype == 0x0c" \
       -T fields -e wlan.sa -e wlan.da -e wlan.fixed.reason_code \
  | sort | uniq -c | sort -rn

# 2. Timing between frames — a script-kiddie tool at 1000/sec looks
#    different from a targeted 3-in-2-sec pattern.
tshark -r storm.pcapng -Y "wlan.fc.type_subtype == 0x0c" \
       -T fields -e frame.time_relative -e wlan.sa

# 3. Reason-code distribution — the flag is often reason code 42
#    or something outside the standard {1,2,3,4,6,7,15} set.
tshark -r storm.pcapng -Y "wlan.fc.type_subtype == 0x0c" \
       -T fields -e wlan.fixed.reason_code | sort -u

# 4. Source-MAC OUI — attacker's OUI may spell something.
```

## The flag surface

- **Unusual reason code.** Values outside the standard set carry
  data in a `2-byte reason field` — the flag is `chr(code)` across
  frames.
- **Inter-frame timing.** Morse-encoded: short gap = dot, long gap =
  dash. Decode the sequence of gaps into a string.
- **Source MAC pattern.** The attacker's MAC changes per frame,
  spelling ASCII across bytes 4-5 of the source addr. Extract with:
  ```
  tshark -r storm.pcapng -Y "wlan.fc.type_subtype == 0x0c" \
         -T fields -e wlan.sa | awk -F: '{ printf "%s%s", $5, $6 }'
  ```
  then hex-decode the string.
- **Destination-MAC list.** The attacker deauthed a specific set of
  clients whose MACs together identify a person / device / flag.
- **Reason-code sequence.** Codes 8,7,10,10,3 → ASCII "hello"
  (codes are 2 bytes; sometimes only the low byte counts).

## Sanity checks

- Reason codes 1..15 are the standard set. Anything else is
  suspicious → probably the flag channel.
- If timing is uniform (100 ms exactly), it's not a Morse channel.
  Look at reason codes and source MACs instead.
- If the source MAC is constant, the flag is in reason codes or
  destinations.

## Cite

- attacks.json: `deauth-broadcast`, `deauth-targeted`.
- IEEE Std 802.11-2020, §9.4.1.7 (Reason Code).
- deauth/reference.md — full reason code table.
