# enterprise/

WPA2/3-Enterprise = **802.1X on top of 802.11**. The AP is the
*authenticator*, not the auth server. The auth server is a RADIUS
speaking EAP inside. Attacks live in three places: the outer EAP
selection, the inner method choice, and the certificate validation
policy on the client.

Companion topics: `hostapd-wpe/`, `eaphammer/`, `freeradius-wpe/`,
`ctf/cert-phish-eap-flags.md`, `ctf/rogue-radius-eap-flag.md`.
