# WPA2 reference

## RSN IE (Element ID 48)

```
Version                 (2 bytes, = 1)
Group Cipher Suite      (4 bytes, OUI 00-0F-AC + selector)
Pairwise Cipher Count   (2 bytes)
Pairwise Cipher List    (4 bytes each — CCMP-128 = 00-0F-AC:04)
AKM Suite Count         (2 bytes)
AKM Suite List          (4 bytes each — PSK = 00-0F-AC:02, EAP = :01)
RSN Capabilities        (2 bytes — MFPC/MFPR bits at 6,7)
PMKID Count             (2 bytes; may be absent in beacon)
PMKID List              (16 bytes each — present in M1 for PMKID leak)
Group Management Cipher (4 bytes — BIP-CMAC-128 = 00-0F-AC:06)
```

Cipher suite selectors — see `security_suites.json`:

| hex | cipher |
| --- | ------ |
| 00-0F-AC:01 | WEP-40 |
| 00-0F-AC:02 | TKIP |
| 00-0F-AC:04 | CCMP-128 |
| 00-0F-AC:05 | WEP-104 |
| 00-0F-AC:06 | BIP-CMAC-128 (group management) |
| 00-0F-AC:08 | GCMP-128 |
| 00-0F-AC:09 | GCMP-256 |

AKM suite selectors:

| hex | AKM |
| --- | --- |
| 00-0F-AC:01 | 802.1X (Enterprise, PMKSA cache) |
| 00-0F-AC:02 | PSK |
| 00-0F-AC:03 | FT-802.1X |
| 00-0F-AC:04 | FT-PSK |
| 00-0F-AC:05 | 802.1X-SHA256 |
| 00-0F-AC:06 | PSK-SHA256 |
| 00-0F-AC:08 | SAE |
| 00-0F-AC:12 | OWE |
| 00-0F-AC:18 | SAE-EXT-KEY (H2E) |

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
