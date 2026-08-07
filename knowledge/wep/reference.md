# WEP reference

## RC4 keystream + 24-bit IV + CRC-32 ICV

WEP encrypts each frame with RC4, keyed by a shared secret (40 or
104 bits) concatenated with a per-frame IV (24 bits). Integrity is
a CRC-32 over the plaintext (the "ICV"). CRC-32 is linear over
XOR — an attacker who flips bits in the ciphertext can flip
corresponding bits in the ICV and the frame still validates.

## The attacks

- **FMS (Fluhrer/Mantin/Shamir 2001)** — weak-IV statistical bias
  in the first bytes of the RC4 keystream leaks key bytes given
  enough weak-IV frames (~250k for 40-bit, ~500k+ for 104-bit).
- **KoreK (2004)** — 17 additional statistical biases refining FMS.
- **PTW (Tews/Weinmann/Pyshkin 2007)** — the practical one.
  Recovers 104-bit WEP in under a minute given ~40k–85k unique IVs.
  aircrack-ng's default WEP attack.
- **ARP-request replay** — replay a captured ARP request to
  generate fresh encrypted frames at line rate, feeding PTW/FMS.
  aireplay-ng --arpreplay.

## Recognition in a beacon

- **No RSN IE** (element 48).
- **No Microsoft WPA1 Vendor-Specific IE** (OUI 00-50-F2:01).
- **Capability Info "Privacy" bit set.**

If you see all three, it's WEP.

## Cite

- IEEE Std 802.11-2016 §12 (superseded but still cites WEP intact).
- Fluhrer, Mantin, Shamir 2001.
- Tews, Weinmann, Pyshkin 2007.
- aircrack-ng documentation.
- attacks.json: `wep-fms`, `wep-korek`, `wep-ptw`,
  `wep-arp-request-replay`.
