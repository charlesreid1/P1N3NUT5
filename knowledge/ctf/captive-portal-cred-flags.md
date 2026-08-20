# Captive-portal cred flags

## The puzzle shape

The AP is open (or PSK-known). Associating drops you into a captive
portal login page. The flag is what a *user* is going to type in
that login page — or, in a variant, the flag is embedded in the
form's HTML / JS / API response.

## Case A — the flag is in the portal itself

Just associate and browse. Read the HTML source, watch network
requests. Common flag hiding places:

- Hidden form fields (`<input type="hidden" name="flag" value="…">`)
- JavaScript variable definitions in the page source
- API responses to XHR requests the portal makes on load
- Referer / cookie / X-Header values the portal echoes back

## Case B — the flag is what a victim types

You stand up your own captive portal on a rogue AP alongside the
target. Victim clients associate to you, hit your portal, type
credentials — those credentials are the flag.

```
# 1. Clone the target SSID.
do_create_rogue_ap(ssid="WCTF-Public", channel=6, security="open",
                   i_own_the_airspace=True)
# 2. Bring up a captive portal that templates the target vendor's
#    login page.
serve_captive_portal(handle=<rogue-handle>, template="basic")
# 3. Deauth clients off the real AP so they reassociate to you.
do_deauth(bssid=<target-bssid>, count=10,
          i_own_the_airspace=True)
# 4. Watch the credential log.
tail -f /tmp/portal-creds.log
```

## Signs a portal IS a trap (defender view)

- Certificate name mismatch — the portal domain doesn't match the
  cert CN.
- HSTS absent — real portals for known-good vendors ship HSTS.
- DNS strangeness — every hostname resolves to the same IP.
- The portal insists on "sign in" for a network the client has
  been on before (real captive portals honor a re-auth cookie).

## What still works when PMF-required

The Case B flow above deauths victims off the real AP to force
reassoc to your open-portal rogue. When the real AP is
PMF-required (or 6 GHz), step 3 `do_deauth` is a no-op — but the
rest of the captive-portal cred-capture flow is intact:

- **Beat the target on RSSI + karma-family attraction.** Stand up
  the rogue louder than the real AP; probing clients that match
  your SSID (via Known Beacons or a matching Probe Response)
  associate on their own, before any deauth would matter.
- **Cold-start clients.** Any client that hasn't associated to
  the real AP yet has no PMF context. Set the twin up early and
  wait — arrivals attach to the loudest match.
- **BTM-forced roam.** If the real AP vendor honors unauth'd
  Category 10 BTM Requests, hint the target toward your rogue
  BSSID; the client cooperates in its own move.
- **Wait for natural reassoc events.** Roams, band steers, and
  AP outages all produce clean reassociation opportunities that
  a louder rogue wins.
- **Case A still works verbatim.** If the flag is *in* the
  portal itself (page source, JS, API response), you never
  needed a victim — just associate to the real AP yourself and
  browse. PMF has no bearing.

## Cite

- attacks.json: `captive-portal-cred-capture`, `evil-twin-clone`,
  `btm-forced-roam`, `mana-known-beacons`.
- knowledge/captive-portal/reference.md.
- knowledge/ctf/pmf-required-targets.md.
