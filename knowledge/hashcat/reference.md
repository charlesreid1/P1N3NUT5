# hashcat reference — WiFi-relevant modes

**Verified against:** hashcat 6.2.x as of 2026-Q3

| mode | name | producer | notes |
| ---- | ---- | -------- | ----- |
| 22000 | WPA-PBKDF2-PMKID+EAPOL | hcxpcapngtool | Modern all-in-one. PMKID and 4-way handshake in one format. |
| 22001 | WPA-PMK-PMKID+EAPOL | (rare) | PMK-side attack; used when PMK is known. |
| 2500 | WPA-EAPOL-PBKDF2 (legacy) | cap2hccapx | Superseded by 22000; still valid input. |
| 2501 | WPA-EAPOL-PMK | | Legacy PMK-side. |
| 16800 | WPA-PMKID-PBKDF2 (legacy) | hcxpcaptool | Superseded by 22000. |
| 16801 | WPA-PMKID-PMK | | Legacy PMK-side. |
| 5500 | NetNTLMv1 / MSCHAPv2 / LEAP | hostapd-wpe, eaphammer, asleap | Inner MSCHAPv2 challenge/response. Input line is `user::domain::<NTResponse_hex>:<ChallengeHash_hex>` — `ChallengeHash` is the 8-byte SHA-1-derived value, not the raw 16-byte PeerChallenge. Derivation callout in `enterprise/reference.md`. Also the correct mode for legacy Cisco LEAP (LEAP uses MSCHAPv2 internally → NetNTLMv1). |
| 4800 | iSCSI CHAP / EAP-MD5 (MD5(chal+pass+salt)) | | Not LEAP — LEAP is 5500. |

## Ergonomics

```
hashcat -m 22000 hs.22000 rockyou.txt         # plain dictionary
hashcat -m 22000 hs.22000 rockyou.txt -r best64.rule
hashcat -m 22000 hs.22000 -a 3 ?d?d?d?d?d?d?d?d   # 8-digit mask
hashcat --session=defcon --restore              # resume interrupted run
hashcat -w 4 -O --status --status-timer=5      # GPU-tuned + status
```

## The 22000 line

```
WPA*<type>*<PMKID/MIC>*<AP_MAC>*<STA_MAC>*<ESSID hex>*<ANonce>*<EAPOL frame>*<MC>
```

- `type=01` → PMKID (M1-only)
- `type=02` → EAPOL 4-way (any subset containing an M2)

## Cite

- hashcat.net wiki — example hashes.
- Steube 2018 — PMKID advisory.
- hcxtools GitHub.
