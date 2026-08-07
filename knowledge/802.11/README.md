# 802.11 — how a modern WiFi session works end-to-end

The frame the whole corpus hangs off. Everything else is a specialization:
WPA2 is 802.11 with a particular RSN IE and 4-way handshake; WPA3 is
802.11 with SAE and PMF-required; PMKID capture is one specific field of
one specific frame in one specific handshake.

See:

- `reference.md` — the 802.11-2020 rollup summary
- `walkthrough.md` — a session end-to-end
- `recognition.md` — what a session looks like in a pcap
