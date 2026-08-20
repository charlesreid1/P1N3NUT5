# Captive portal reference

The WCTF favorite: the flag is often literally what a user types into a
login form served by your rogue AP.

## The chain

```
client associates ──► DHCP lease ──► DNS query ──► HTTP redirect ──► login form
                                                                       │
                                                                       ▼
                                                                  cred capture
```

Every layer of that chain runs on the Pineapple. Layers:

1. **DHCP** — dnsmasq issues the lease and points DNS at itself
   (`dhcp-option=6,172.16.42.1`).
2. **DNS** — dnsmasq intercepts every A query and returns the
   Pineapple's IP (`address=/#/172.16.42.1`).
3. **HTTP** — nginx or the evil-portal module serves the login page
   for every URL, with a 302 to the templated portal.
4. **Portal template** — matches the target vendor's branding
   (Xfinity, Starbucks, corporate SSO). eaphammer / wifipumpkin3 ship
   templates.
5. **Cred capture** — form POST goes to a logger.

## Signs a captive portal is a trap

- Cert-name mismatch (Pineapple's self-signed vs the vendor's real CA)
- Absent HSTS on the portal domain
- Weird DNS — every hostname resolves to the same IP
- The portal insists on Wi-Fi Alliance-style "sign in" for what
  should be an already-provisioned SSID

## Cite

- IETF RFC 8908 — Captive Portal API (modern OS probe URLs).
- IETF RFC 7710 — Captive-Portal Identification Using DHCP or RA
  (option 114, obsoleted by RFC 8910 but still cited by legacy stacks).
- IETF RFC 8910 — Captive-Portal Identification in DHCP + RA
  (modernized replacement for RFC 7710; ties DHCP option 114 to the
  RFC 8908 API URL).
- Hak5 evil-portal module docs.
- hostapd configuration reference.
