# PMKID recognition — is this AP a fastpath?

Not every WPA2 AP leaks PMKID. Recognition means predicting whether
`hcxdumptool` will yield a PMKID before you spend capture time.

## Passive tell — RSN IE PMKID Count

The beacon's RSN IE has a `PMKID Count` field. Values:

- **0** — the AP is not caching PMKIDs at beacon time. Doesn't
  guarantee it won't emit one in M1, but a non-zero count strongly
  predicts one will.
- **>= 1** — the AP is advertising cached PMKSAs. Almost certainly
  will emit PMKID in M1.

Read with tshark:

```
tshark -r beacon.pcapng \
  -Y "wlan.tag.number == 48" \
  -T fields -e wlan.bssid -e wlan.rsn.pmkid.count
```

## Active tell — send one association

The definitive check: send a single Association Request, capture the
AP's M1, read the EAPOL-Key IE. If a PMKID subfield is present, the
attack path is open.

`hcxdumptool` in single-target mode does this in about 2 seconds.

## Vendor heuristics (2026)

- **Most consumer ISP-issued routers** — still leak PMKID by default.
- **Enterprise gear (Cisco, Aruba, Ruckus, Extreme)** — recent
  firmwares disable PMKID emission unless PMKSA caching is in use.
- **Consumer mesh (Eero, Google Nest, TP-Link Deco)** — mixed;
  varies with firmware generation.
- **OpenWRT / dd-wrt** — leaks by default.

Corpus record: `pmkid-capture` with `still_effective_2026: true`.

## When it's NOT leaked

- AP firmware sets `okc=0` and disables PMKSA caching entirely.
- WPA3-SAE-only (there is no PMKID field in the SAE handshake).
- Some Aruba / Cisco Wave-2 firmwares that PMKID-only-under-11r.

## Cite

- IEEE Std 802.11-2020, §9.4.2.24 (RSN Element), §12.7 (PMKSA cache).
- Steube 2018.
