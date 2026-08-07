# 4-way handshake — corner cases

The canonical WPA2/3 handshake is covered in `wpa2/reference.md`. This
file is the corner-case catalog for capture and conversion.

## Minimum sufficient set for hashcat

- **M1 alone** — sufficient only if it carries a PMKID (Steube 2018).
  hashcat 22000 tag `WPA*01`.
- **M1 + M2** — the classic. M2 carries the MIC that hashcat validates.
  Tag `WPA*02`.
- **M2 + M3** — also works; M3 carries the same MIC keyed with the same
  KCK. Rare in captures because M2 arrives first, but hcxpcapngtool
  will pair them.
- **All four** — no advantage over M1+M2. Wireshark
  `wlan.enable_decryption` needs the full 4-way to derive PTK for
  offline decryption.

## PMF-protected disassoc

If the target AP advertises PMF-required and the client is PMF-capable,
disassoc/deauth frames from us are dropped. Alternatives:

- Wait for a natural roam / reboot.
- Trigger Kr00k (disassoc still works but the tail-frame decryption is
  the goal, not a handshake).
- SSID Confusion — the client believes it's on network X.

## 802.11r FT reassoc capture

When a client roams between two APs in the same Mobility Domain, the
reassociation carries an M1-analogue that hashcat 22000 handles. Look
for an MDE IE (Element ID 54) in the beacon; the roam produces the
capture on the destination AP's channel.

## Cite

- IEEE Std 802.11-2020, §12.7 (4-Way Handshake), §12.11 (FT).
- hcxtools GitHub — hcxpcapngtool README.
