# post-crack-rf

The last-mile once you have a PSK or an EAP credential. Strictly
RF-adjacent — this dir ends at "you are on the network."

**Explicit scope stop.** Kerberoasting, Responder, mitm6, SMB, LDAP,
service scans — all out. If a WCTF flag lives past this line, that's
a LAN pentest problem outside P1N3NUT5. Hand off to a general
pentest toolkit outside this MCP.

The three engagements this dir covers:

1. **Decrypt a captured pcap** with a recovered PSK — get at flag
   bytes inside encrypted 802.11 data frames.
2. **Validate a candidate PSK** — trial-decrypt an existing capture
   to confirm before you spend more attack time.
3. **Join the network as a legitimate STA** — verify that the
   credential works and, when the flag is a resource on the LAN,
   set up the handoff.

Companion: `pcap/`, `wpa2/`, `wpa3/`, `hashcat/`.
