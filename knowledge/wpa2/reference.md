# WPA2 reference

## RSN IE (Element ID 48)

```
Version                 (2 bytes, = 1)
Group Cipher Suite      (4 bytes, OUI 00-0F-AC + selector)
Pairwise Cipher Count   (2 bytes)
Pairwise Cipher List    (4 bytes each — CCMP-128 = 00-0F-AC:04)
AKM Suite Count         (2 bytes)
AKM Suite List          (4 bytes each — PSK = 00-0F-AC:02, EAP = :01)
RSN Capabilities        (2 bytes — MFPR bit 6, MFPC bit 7)
PMKID Count             (2 bytes; may be absent in beacon)
PMKID List              (16 bytes each — present in M1 for PMKID leak)
Group Management Cipher (4 bytes — BIP-CMAC-128 = 00-0F-AC:06)
```

Cipher suite selectors — see `security_suites.json`. The trailing byte
in each selector is the decimal cipher-suite number (0x04 = 4 = CCMP-128).

| hex           | dec | cipher                          |
| ---           | --- | ------                          |
| 00-0F-AC:01   | 1   | WEP-40                          |
| 00-0F-AC:02   | 2   | TKIP                            |
| 00-0F-AC:04   | 4   | CCMP-128                        |
| 00-0F-AC:05   | 5   | WEP-104                         |
| 00-0F-AC:06   | 6   | BIP-CMAC-128 (group management) |
| 00-0F-AC:08   | 8   | GCMP-128                        |
| 00-0F-AC:09   | 9   | GCMP-256                        |
| 00-0F-AC:0A   | 10  | CCMP-256                        |
| 00-0F-AC:0B   | 11  | BIP-GMAC-128 (group management) |
| 00-0F-AC:0C   | 12  | BIP-GMAC-256 (group management) |
| 00-0F-AC:0D   | 13  | BIP-CMAC-256 (group management) |

AKM suite selectors. Per IEEE 802.11-2020 Table 9-151:

| hex           | AKM dec | Key management                                    |
| ---           | ---     | ---                                               |
| 00-0F-AC:01   | 1       | 802.1X (Enterprise, PMKSA cache)                  |
| 00-0F-AC:02   | 2       | PSK                                               |
| 00-0F-AC:03   | 3       | FT-802.1X                                         |
| 00-0F-AC:04   | 4       | FT-PSK                                            |
| 00-0F-AC:05   | 5       | 802.1X-SHA256                                     |
| 00-0F-AC:06   | 6       | PSK-SHA256                                        |
| 00-0F-AC:07   | 7       | TDLS                                              |
| 00-0F-AC:08   | 8       | SAE                                               |
| 00-0F-AC:09   | 9       | FT-SAE                                            |
| 00-0F-AC:0B   | 11      | 802.1X Suite-B 128 (SHA-256)                      |
| 00-0F-AC:0C   | 12      | 802.1X Suite-B 192 (SHA-384) / WPA3-Ent 192-bit   |
| 00-0F-AC:0D   | 13      | FT-802.1X-SHA384                                  |
| 00-0F-AC:0E   | 14      | FILS-SHA256                                       |
| 00-0F-AC:0F   | 15      | FILS-SHA384                                       |
| 00-0F-AC:10   | 16      | FT-FILS-SHA256                                    |
| 00-0F-AC:11   | 17      | FT-FILS-SHA384                                    |
| 00-0F-AC:12   | 18      | OWE                                               |
| 00-0F-AC:13   | 19      | FT-PSK-SHA384                                     |
| 00-0F-AC:14   | 20      | PSK-SHA384                                        |
| 00-0F-AC:18   | 24      | SAE-EXT-KEY (GCMP-256 / SHA-384 extended-key)     |
| 00-0F-AC:19   | 25      | FT-SAE-EXT-KEY                                    |

Hex-vs-decimal caveat: the trailing byte is the AKM number in hex,
NOT in decimal — 0x18 = decimal 24 (SAE-EXT-KEY), NOT decimal 18
(OWE). H2E is signaled via the RSNXE (IE 244) H2E-only bit, not by
any specific AKM number. See [[akm-selector-glossary]].

## 4-way handshake (EAPOL-Key, EtherType 0x888E)

```
      AP ─────────────────────────────── STA
       │      M1  ANonce + PMKID*     │   * optional; present ⇒ Steube 2018 crack path
       │ ──────────────────────────►   │
       │                                │
       │      M2  SNonce + MIC          │
       │ ◄──────────────────────────    │   MIC keyed with KCK (derived from PTK)
       │                                │
       │      M3  GTK + ANonce + MIC    │
       │ ──────────────────────────►   │
       │                                │
       │      M4  ACK + MIC             │
       │ ◄──────────────────────────    │
```

Cracking needs M1+M2 minimum (M2 carries the MIC that hashcat validates);
M2+M3 also works. hashcat mode 22000 accepts either shape via
`hcxpcapngtool`.

## Cite

- IEEE Std 802.11-2020, §12.7 (Key management), §9.4.2.24 (RSN IE).
- Steube 2018 — PMKID attack (hashcat forum thread 7717).
