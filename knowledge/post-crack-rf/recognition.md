# post-crack-rf — recognition

## When is the crack "done enough" to hand off?

The right stopping condition depends on the flag surface:

- **PSK is the flag** — the moment `hashcat --status` shows the
  cracked entry, you're done. No association, no decrypt, no
  handshake to complete. Stop.
- **Data-frame decrypt is the flag** — you need the 4-way + PSK,
  then Path A of the walkthrough. Association not required.
- **Flag is on the LAN behind the AP** — you need Path C
  association + DHCP. This is a LAN pentest handoff; note the
  scope stop.

## Do I need to associate?

**Almost never for a WCTF WPA-PSK puzzle.**

- Passive capture + offline decrypt is stealthier, faster, and
  doesn't disturb other clients.
- Association may deauth other STAs, trip a WIDS, or leave a
  visible entry in the AP's association table.

Reasons you *would* associate:

1. The flag is reachable only via a normal client association
   (a HTTP resource on the AP, an SNMP-only device, a
   captive-portal page that only serves the flag after auth).
2. The recovered PSK is not obviously a flag and you want to
   validate operationally.
3. You need to verify a Passpoint/OSU flow.

## Signals the decrypt worked

- LLC/SNAP header visible at the start of the decrypted frame
  (`0xAA 0xAA 0x03 0x00 0x00 0x00`).
- EtherType field is sensible (`0x0800` IP, `0x0806` ARP,
  `0x86DD` IPv6, `0x888E` EAPOL).
- Wireshark's "IEEE 802.11" pane shows a "Data" subframe expandable
  into IP / TCP / DNS.

Signals the decrypt did NOT work:

- Frame body is high-entropy bytes.
- Wireshark warning "unable to decrypt data" in the info column.

## Signals the association worked

- `wpa_cli status` shows `wpa_state=COMPLETED`.
- DHCP lease received (`ip addr` shows an address on the target
  subnet).
- The AP's beacon still names the client's MAC as associated
  (visible in `iw dev wlan0 station dump` from a separate radio in
  monitor mode).

## When the "crack" was actually wrong

- `hashcat` reported a match but the passphrase doesn't
  decrypt. False positives are vanishingly rare on WPA2 but not
  impossible if the `.22000` file was corrupt.
- The passphrase decrypts *some* frames but not others — usually a
  mismatched ESSID (case-sensitive), or a mixed capture with
  multiple ESSIDs.

## Cite

- Wireshark 802.11 decryption docs.
- IEEE Std 802.11-2020, §12.7.
