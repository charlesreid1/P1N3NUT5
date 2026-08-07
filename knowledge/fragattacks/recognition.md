# FragAttacks — recognition

Twelve CVEs across three primitives. Not every stack is vulnerable
to all three; recognition is which primitive to try first.

## Vulnerability by primitive

### A-MSDU flag confusion (CVE-2020-24588)

Broad hit. Almost every stack was vulnerable in 2020; most patched
by 2022. Vulnerable-then-not signal:

- **Behavior test.** Vanhoef's `test-tool` sends an A-MSDU-flagged
  frame; a vulnerable client's IP stack sees an incoming ping that
  a non-vulnerable one drops.
- **OS / firmware version** — check the vendor's advisory. Cisco,
  Aruba, Ruckus, most consumer OEMs had patches in 2021.

### Mixed-key fragment reassembly (CVE-2020-24587)

Narrower. Requires specific behavior around rekey + fragment cache.

- **How often does the target rekey?** Some deployments rekey every
  hour, some every 24 hours, some never. Rare rekey = rare
  opportunity.
- **Does the target support fragmentation at all?** Modern high-
  bandwidth clients rarely receive fragmented frames; the attack
  surface exists only if the AP or a legitimate peer sends
  fragments.

### Fragment cache poisoning at connect (CVE-2020-24586)

Rarer implementation bug. Vulnerable-then-not signal:

- Client-side driver behavior on disconnect; not exposed via probes.
- Vanhoef's `test-tool` includes a cache-clear check.

## Cross-primitive signals

- **Stack modernity.** Any WiFi stack shipped in 2022+ probably has
  the base patches. ESP32 firmware < 4.x, some older Marvell and
  Realtek drivers — vulnerable.
- **Fragmentation support advertised.** Beacon Fragmentation
  Threshold field being reasonable-sized means the AP fragments;
  otherwise, mixed-key doesn't apply.
- **A-MSDU support advertised.** HT Capabilities IE has an "A-MSDU
  supported" bit. Almost always set on modern stacks.

## What a vulnerable session looks like

- **A-MSDU flag confusion succeeded** — target replies to a ping
  the attacker injected as plaintext inside an encrypted BSS.
- **Mixed-key reassembly succeeded** — target processes a frame
  whose fragment-1 and fragment-2 were encrypted with different
  keys.
- **Cache poison succeeded** — target processes a frame whose
  fragments were laid down before the client's connect.

## What a WIDS sees

- Anomalous A-MSDU frames with plaintext inner content.
- Rekey followed by unusual fragment-reassembly activity.
- Injected frames from a source MAC that never associated to the AP.

## When to skip FragAttacks

- **Modern flagship OS.** iOS 15+/Android 12+/Windows 11 all have
  patches. Move to KRACK, Kr00k, SSID Confusion, or transition-
  mode downgrade depending on other signals.
- **PMF-required + no rekey window.** Path B closes; only A-MSDU
  flag confusion remains and that's patched broadly.

## Cite

- Vanhoef 2020 — Fragment and Forge.
- vanhoefm/fragattacks — `test-tool` for per-target vulnerability
  probing.
- CVE-2020-24586..24588 (12 CVEs total).
- IEEE Std 802.11-2020, §9.7 (fragmentation), §5.1.5 (A-MSDU).
