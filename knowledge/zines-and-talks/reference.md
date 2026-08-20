# Zines and talks — the canon

Landmark talks and papers, in one place. Each entry names the venue
year, the primary artifact, and the bibliography id.

## The theory + core practice

- **2001 — Fluhrer, Mantin, Shamir.** *Weaknesses in the Key
  Scheduling Algorithm of RC4.* SAC 2001. WEP dies. → `fms-2001`
- **2004 — KoreK.** WEP attack refinements (NetStumbler forum
  posts). → `korek-2004`
- **2007 — Tews, Weinmann, Pyshkin.** *Breaking 104 bit WEP in less
  than 60 seconds.* WISA 2007. Practical WEP. → `ptw-2007`
- **2008 — Beck, Tews.** *Practical attacks against WEP and WPA.*
  TKIP MIC recovery. TKIP dies. → `beck-tews-2008`
- **2011 — Viehböck.** *Brute forcing Wi-Fi Protected Setup.*
  Reaver's foundation. → `viehboeck-wps-2011`
- **2014 — Bongard.** *Offline bruteforce attack on WPS / Pixie
  Dust.* Passwords^14. WPS is done. → `bongard-pixie-2014`
- **2004 — Dino Dai Zovi & Shane "K2" Macaulay.** *All Your Layer
  Are Belong To Us.* Black Hat USA / DEF CON 12. Original KARMA.
  → `karma-daizovi-macaulay-2004`
- **2012 — Glenn Wilkinson (SensePost).** *Snoopy: A distributed
  tracking and profiling framework.* Black Hat Abu Dhabi 2012.
  Passive probe correlation for geo-tracking. → `wilkinson-snoopy-2012`
- **2014 — SensePost.** *Manna from Heaven.* DEF CON 22. KARMA
  reborn. → `sensepost-mana-2014`

## The Vanhoef era

- **2017 — Vanhoef, Piessens.** *Key Reinstallation Attacks.* CCS
  2017. KRACK. → `vanhoef-krack-2017`
- **2017 — Artenstein.** *Broadpwn.* Black Hat USA 2017. WiFi
  chipset RCE. → `artenstein-broadpwn-2017`
- **2018 — Steube.** *New attack on WPA/WPA2 using PMKID.* hashcat
  forum thread 7717. Client-free capture. → `steube-pmkid-2018`
- **2017–2018 — Etizaz Mohsin (Bastille Networks).** *Known Beacons.*
  SSID-dictionary beacon flood; landed in wifite2 / hostapd-mana.
  → `known-beacons-2017` (bastille.net/research/vulnerabilities/known-beacons/;
  WPA-Sec archive: wpa-sec.stanev.org/?attacks)
- **2018 — Vanhoef, Piessens.** *Release the Kraken: New KRACKs in
  the 802.11 Standard.* CCS 2018. Multi-channel MitM (MC-MitM).
  → `vanhoef-mcmitm-2018`
- **2019 — Vanhoef, Ronen.** *Dragonblood.* IEEE S&P 2020. WPA3-SAE
  side channels. → `vanhoef-dragonblood-2019`
- **2019 — ESET.** *Kr00k.* CVE-2019-15126. All-zero PTK on
  disassoc. → `eset-kr00k-2020`
- **2021 — Vanhoef.** *Fragment and Forge.* USENIX Security 2021.
  FragAttacks. → `vanhoef-fragattacks-2021`
- **2023 — Vanhoef.** *Framing Frames.* USENIX Security 2023.
  Power-save queue poisoning. → `vanhoef-framing-frames-2023`
- **2023 — Vanhoef.** *MacStealer.* Black Hat Asia 2023. →
  `vanhoef-macstealer-2023`
- **2024 — Héloïse Gollier, Mathy Vanhoef.** *SSID Confusion:
  Making Wi-Fi Clients Connect to the Wrong Network.* CVE-2023-52424,
  co-disclosed 2024-05-14 at KU Leuven / DistriNet.
  → `vanhoef-yseboodt-ssid-2024`

## Wi-Fi 7 / MLO research (2023+)

- **2023 — Kachhwaha, Chattopadhyay et al.** *Security Analysis of
  IEEE 802.11be Multi-Link Operation (MLO).* Early MLO surface
  analysis; queue-race / per-link PTKSA hierarchy.
- **2024 — Vanhoef et al.** ongoing MLO / Wi-Fi 7 vulnerability
  disclosures at USENIX Security. Cross-link race conditions and
  new deauth-on-MLO behavior.

## Tooling talks

- **Gabriel Ryan.** eaphammer release + associated DEF CON / BSides
  talks on cert-phish and inner-EAP downgrade (2017–2020). →
  `gabrielryan-eaphammer`
- **Josh Wright.** asleap (LEAP / MSCHAPv2 offline dictionary
  attack); "Hacking Exposed Wireless" reference. → `wright-asleap`,
  `wright-hacking-exposed-wireless-3e`
- **blasty.** upc_keys and the vendor default-PSK derivation
  ecosystem. → `upc-keys-repo`

## Standards + certification

- **IEEE Std 802.11-2020** — the current rollup. §12 (security)
  and §11.34 (PMF) are the load-bearing chapters. → `ieee-802-11-2020`
- **IEEE Std 802.11ax-2021** — Wi-Fi 6 / 6E. → `ieee-802-11ax-2021`
- **IEEE Std 802.11be-2024** — Wi-Fi 7 (MLO). → `ieee-802-11be-2024`
- **Wi-Fi Alliance WPA3 spec.** → `wfa-wpa3-spec`
- **Wi-Fi Alliance WPS 2.0 spec.** → `wfa-wps-2-0`

## Cite

- All bibliography ids resolve in `records/bibliography.json`.
- Pointers, not paraphrase — every talk above has its primary source
  linked from the bib record.
