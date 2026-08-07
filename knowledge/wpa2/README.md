# WPA2 — the modern workhorse

WPA2-Personal (PSK) and WPA2-Enterprise (802.1X). Still the primary
DEFCON WCTF target in 2026. All of the crack paths converge on the
4-way handshake or the M1 PMKID; both feed hashcat mode 22000.

- `reference.md` — byte-by-byte handshake, RSN IE fields
- `walkthrough.md` — capture, convert, crack
- `recognition.md` — beacon RSN IE inspection
