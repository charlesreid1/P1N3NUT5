# FragAttacks

Vanhoef 2020 (USENIX Security 2021). 12 CVEs targeting frame
aggregation and fragmentation. Two headline primitives:

## 1. A-MSDU flag confusion (CVE-2020-24588)

The 802.11 header has an "Is Aggregate" bit distinguishing normal
QoS data frames from A-MSDU (Aggregated MAC Service Data Unit)
frames. Many stacks accept A-MSDU frames even when the bit is not
protected by encryption — an attacker can inject plaintext that
the client parses as an A-MSDU subframe destined for the client
itself. Bypasses encryption for that specific traffic path.

## 2. Mixed-key fragment cache (CVE-2020-24587)

Fragments sent under different keys are still reassembled in a
shared cache. An attacker can send fragment #1 under an old
(pre-rekey) key and fragment #2 under a new key; the reassembled
frame contains attacker-controlled content the receiver treats
as authenticated.

## The others

CVE-2020-24586 (fragmentation cache not cleared on
(re)connect) plus a set of implementation-specific bugs — some
stacks accept plaintext broadcast fragments even inside a WPA2
network, etc. See the paper for the full enumeration.

## Setup

MC-MitM plus crafted-frame injection (scapy Dot11 with the
appropriate FCfield bits). Public PoC scripts ship with the
2020 disclosure.

## 2026 status

Vendor patches available since 2021. Coverage is uneven — many
IoT stacks (thin WiFi front-ends, ESP32 variants pre-firmware-4)
remain vulnerable.

## Cite

- Vanhoef 2020 — Fragment and Forge (USENIX Security 2021).
- CVE-2020-24586..24588 (12 CVEs total in the family).
- attacks.json: `fragattacks-plaintext-inject`,
  `fragattacks-mixed-key`.
