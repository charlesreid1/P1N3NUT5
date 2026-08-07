#!/usr/bin/env python3
"""
Depth-pass enrichment for frame_types.json + ies.json.

Implements Phase D2 (F1, F2, I1, I2, I3) from plan-improve-docs.md:
  F1. technical_body.fields[] byte layout per frame type — {name, offset_bytes,
      length_bytes, notes}.
  F2. wctf_uses extended so lookup_frame returns a consistent shape.
  I1. technical_body.layout[] byte layout per IE — {name, offset_bytes,
      length_bytes, notes}.
  I2. ~6 ANQP-element records (nai-realm, roaming-consortium, venue-info, etc.).
  I3. Add ie-mde / ie-anqp shorter slugs as aliases.

Layouts follow IEEE 802.11-2020 §9. IE offsets are into the element BODY
(i.e. after the 2-byte Element ID + Length header) unless otherwise
noted. Frame offsets are from the beginning of the 802.11 header.

Non-priority IEs get a truncated placeholder `layout: [{name: "opaque",
notes: "see IEEE 802.11-2020 §9.4"}]` — that lets the schema stay
uniform without pretending we've decoded every one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RECORDS = Path(__file__).resolve().parent.parent / "knowledge" / "records"
FRAMES = RECORDS / "frame_types.json"
IES = RECORDS / "ies.json"


# ---------------------------------------------------------------------------
# F1 — frame byte layouts. Offsets are from start of the MAC header (byte 0)
# unless the frame has a distinct carrier (EAPOL-Key inside a QoS Data frame).
# ---------------------------------------------------------------------------

FRAME_LAYOUTS: dict[str, list[dict]] = {
    "frame-mgmt-deauth": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2,
         "notes": "type=0 (mgmt), subtype=12 (deauth)"},
        {"name": "Duration/ID", "offset_bytes": 2, "length_bytes": 2,
         "notes": "microsecond NAV, or zero for broadcast"},
        {"name": "Address 1 (DA)", "offset_bytes": 4, "length_bytes": 6,
         "notes": "destination — ff:ff:ff:ff:ff:ff for broadcast deauth"},
        {"name": "Address 2 (SA)", "offset_bytes": 10, "length_bytes": 6,
         "notes": "source — the AP BSSID"},
        {"name": "Address 3 (BSSID)", "offset_bytes": 16, "length_bytes": 6,
         "notes": "same as SA in AP→STA direction"},
        {"name": "Sequence Control", "offset_bytes": 22, "length_bytes": 2,
         "notes": "fragment number (4 bits) + sequence number (12 bits)"},
        {"name": "Reason Code", "offset_bytes": 24, "length_bytes": 2,
         "notes": "IEEE 802.11-2020 §9.4.1.7 — 1 (unspecified) / 3 (leaving BSS) / 7 (nonassoc STA) / 15 (4-way timeout)"},
    ],
    "frame-mgmt-disassoc": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=0, subtype=10"},
        {"name": "Duration/ID", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "Address 1 (DA)", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "Address 2 (SA)", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
        {"name": "Address 3 (BSSID)", "offset_bytes": 16, "length_bytes": 6, "notes": ""},
        {"name": "Sequence Control", "offset_bytes": 22, "length_bytes": 2, "notes": ""},
        {"name": "Reason Code", "offset_bytes": 24, "length_bytes": 2,
         "notes": "same reason-code space as deauth"},
    ],
    "frame-mgmt-beacon": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=8; DA=ff:ff:ff:ff:ff:ff"},
        {"name": "Timestamp", "offset_bytes": 24, "length_bytes": 8,
         "notes": "AP's TSF timer (microseconds since AP boot)"},
        {"name": "Beacon Interval", "offset_bytes": 32, "length_bytes": 2,
         "notes": "TU count between beacons; typically 100 TU (102.4 ms)"},
        {"name": "Capability Info", "offset_bytes": 34, "length_bytes": 2,
         "notes": "ESS/IBSS/Privacy/Short Preamble/PBCC/Channel Agility/Spectrum Mgmt/QoS/… bits"},
        {"name": "Information Elements", "offset_bytes": 36, "length_bytes": None,
         "notes": "variable — SSID (0), Supported Rates (1), DS Parameter (3), TIM (5), Country (7), RSN (48), HT/VHT/HE/EHT Cap, WPS (221), Vendor-Specific (221). See ies.json for byte layouts."},
    ],
    "frame-mgmt-probe-request": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=4; SA=STA, DA=broadcast or target BSSID"},
        {"name": "Information Elements", "offset_bytes": 24, "length_bytes": None,
         "notes": "SSID (0), Supported Rates (1), Extended Supported Rates (50), HT Cap (45), Extended Cap (127), Vendor-Specific (221). Client-fingerprint IE order matters."},
    ],
    "frame-mgmt-probe-response": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=5; DA=probing STA"},
        {"name": "Timestamp", "offset_bytes": 24, "length_bytes": 8, "notes": "AP TSF timer"},
        {"name": "Beacon Interval", "offset_bytes": 32, "length_bytes": 2, "notes": ""},
        {"name": "Capability Info", "offset_bytes": 34, "length_bytes": 2, "notes": ""},
        {"name": "Information Elements", "offset_bytes": 36, "length_bytes": None,
         "notes": "same IE set as beacon; unicast to the probing STA"},
    ],
    "frame-mgmt-auth": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=11"},
        {"name": "Authentication Algorithm", "offset_bytes": 24, "length_bytes": 2,
         "notes": "0=Open, 1=Shared Key (WEP), 2=Fast BSS Transition, 3=SAE (WPA3)"},
        {"name": "Authentication Transaction Sequence Number", "offset_bytes": 26, "length_bytes": 2,
         "notes": "for SAE: 1=Commit, 2=Confirm"},
        {"name": "Status Code", "offset_bytes": 28, "length_bytes": 2,
         "notes": "0=success"},
        {"name": "Payload", "offset_bytes": 30, "length_bytes": None,
         "notes": "SAE Commit/Confirm carries the finite-field scalar+element or the confirm-hash"},
    ],
    "frame-mgmt-assoc-request": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=0"},
        {"name": "Capability Info", "offset_bytes": 24, "length_bytes": 2, "notes": ""},
        {"name": "Listen Interval", "offset_bytes": 26, "length_bytes": 2,
         "notes": "beacon intervals the STA sleeps for"},
        {"name": "Information Elements", "offset_bytes": 28, "length_bytes": None,
         "notes": "SSID (0), Supported Rates (1), RSN (48), Extended Cap (127), HT/VHT Cap"},
    ],
    "frame-mgmt-assoc-response": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=1"},
        {"name": "Capability Info", "offset_bytes": 24, "length_bytes": 2, "notes": ""},
        {"name": "Status Code", "offset_bytes": 26, "length_bytes": 2,
         "notes": "0=success"},
        {"name": "AID (Association ID)", "offset_bytes": 28, "length_bytes": 2,
         "notes": "assigned by AP"},
        {"name": "Information Elements", "offset_bytes": 30, "length_bytes": None,
         "notes": "Supported Rates + AP's HT/VHT/HE Cap"},
    ],
    "frame-mgmt-reassoc-request": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=2"},
        {"name": "Capability Info", "offset_bytes": 24, "length_bytes": 2, "notes": ""},
        {"name": "Listen Interval", "offset_bytes": 26, "length_bytes": 2, "notes": ""},
        {"name": "Current AP Address", "offset_bytes": 28, "length_bytes": 6,
         "notes": "previous AP BSSID"},
        {"name": "Information Elements", "offset_bytes": 34, "length_bytes": None,
         "notes": "SSID, RSN, MDE (11r), FTE (11r)"},
    ],
    "frame-mgmt-reassoc-response": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=0, subtype=3"},
        {"name": "Capability Info", "offset_bytes": 24, "length_bytes": 2, "notes": ""},
        {"name": "Status Code", "offset_bytes": 26, "length_bytes": 2, "notes": ""},
        {"name": "AID", "offset_bytes": 28, "length_bytes": 2, "notes": ""},
        {"name": "Information Elements", "offset_bytes": 30, "length_bytes": None,
         "notes": "FTE for 11r roams"},
    ],
    "frame-mgmt-action": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=0, subtype=13"},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1,
         "notes": "0=Spectrum Mgmt, 3=Block Ack, 4=Public (GAS), 5=Radio Measurement, 6=Fast BSS Transition, 7=HT, 10=WNM, 11=RRM, …"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1,
         "notes": "category-specific action code (e.g. WNM/BTM Request = category 10 action 7)"},
        {"name": "Action Payload", "offset_bytes": 26, "length_bytes": None,
         "notes": "category+action-specific — see IEEE 802.11-2020 §9.6"},
    ],
    "frame-ctrl-rts": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=11"},
        {"name": "Duration", "offset_bytes": 2, "length_bytes": 2,
         "notes": "microseconds until CTS+DATA+ACK completes — the NAV grab"},
        {"name": "Receiver Address (RA)", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "Transmitter Address (TA)", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
        {"name": "FCS", "offset_bytes": 16, "length_bytes": 4, "notes": ""},
    ],
    "frame-ctrl-cts": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=12"},
        {"name": "Duration", "offset_bytes": 2, "length_bytes": 2, "notes": "NAV setting"},
        {"name": "Receiver Address (RA)", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "FCS", "offset_bytes": 10, "length_bytes": 4, "notes": ""},
    ],
    "frame-ctrl-ack": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=13"},
        {"name": "Duration", "offset_bytes": 2, "length_bytes": 2, "notes": "usually 0"},
        {"name": "Receiver Address (RA)", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "FCS", "offset_bytes": 10, "length_bytes": 4, "notes": ""},
    ],
    "frame-ctrl-ps-poll": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=10"},
        {"name": "AID", "offset_bytes": 2, "length_bytes": 2, "notes": "STA's association ID (high 2 bits set)"},
        {"name": "BSSID", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "Transmitter Address", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
    ],
    "frame-ctrl-blockack-req": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=8"},
        {"name": "Duration", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "RA", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "TA", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
        {"name": "BAR Control", "offset_bytes": 16, "length_bytes": 2, "notes": ""},
        {"name": "Starting Sequence Control", "offset_bytes": 18, "length_bytes": 2, "notes": ""},
    ],
    "frame-ctrl-blockack": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=9"},
        {"name": "Duration", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "RA", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "TA", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
        {"name": "BA Control", "offset_bytes": 16, "length_bytes": 2, "notes": ""},
        {"name": "BA Info", "offset_bytes": 18, "length_bytes": None,
         "notes": "SSN + Bitmap; variable length"},
    ],
    "frame-ctrl-trigger": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=2 (802.11ax)"},
        {"name": "Duration", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "RA", "offset_bytes": 4, "length_bytes": 6, "notes": "broadcast for multi-STA triggers"},
        {"name": "TA", "offset_bytes": 10, "length_bytes": 6, "notes": "AP MAC"},
        {"name": "Common Info", "offset_bytes": 16, "length_bytes": 8,
         "notes": "Trigger Type / UL Length / More TF / CS Required / UL BW / GI+LTF Type / MU-MIMO HE-LTF / UL STBC / LDPC Extra / AP TX Power / …"},
        {"name": "User Info List", "offset_bytes": 24, "length_bytes": None,
         "notes": "per-user 5-byte or larger sub-fields — RU allocation, UL MCS, dcm, coding, SS allocation"},
    ],
    "frame-ctrl-cf-end": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=1, subtype=14"},
        {"name": "Duration", "offset_bytes": 2, "length_bytes": 2, "notes": "0 (end of CF period)"},
        {"name": "RA", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "BSSID", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
    ],
    "frame-data": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=2, subtype=0 (legacy Data)"},
        {"name": "Duration/ID", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "Address 1", "offset_bytes": 4, "length_bytes": 6, "notes": "RA — recipient"},
        {"name": "Address 2", "offset_bytes": 10, "length_bytes": 6, "notes": "TA — transmitter"},
        {"name": "Address 3", "offset_bytes": 16, "length_bytes": 6, "notes": "DA or SA depending on ToDS/FromDS"},
        {"name": "Sequence Control", "offset_bytes": 22, "length_bytes": 2, "notes": ""},
        {"name": "Payload", "offset_bytes": 24, "length_bytes": None,
         "notes": "encrypted under CCMP/GCMP if Privacy bit set"},
    ],
    "frame-data-qos-data": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=2, subtype=8 (QoS Data)"},
        {"name": "Duration/ID", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "Address 1", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "Address 2", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
        {"name": "Address 3", "offset_bytes": 16, "length_bytes": 6, "notes": ""},
        {"name": "Sequence Control", "offset_bytes": 22, "length_bytes": 2, "notes": ""},
        {"name": "QoS Control", "offset_bytes": 24, "length_bytes": 2,
         "notes": "TID (4 bits), A-MSDU bit (FragAttacks surface), AckPolicy"},
        {"name": "Payload", "offset_bytes": 26, "length_bytes": None,
         "notes": "encrypted CCMP/GCMP payload — user data or LLC+EAPOL-Key carrier"},
    ],
    "frame-data-null": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=2, subtype=4"},
        {"name": "Duration/ID", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "Address 1", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "Address 2", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
        {"name": "Address 3", "offset_bytes": 16, "length_bytes": 6, "notes": ""},
        {"name": "Sequence Control", "offset_bytes": 22, "length_bytes": 2, "notes": ""},
    ],
    "frame-qos-null-data": [
        {"name": "Frame Control", "offset_bytes": 0, "length_bytes": 2, "notes": "type=2, subtype=12; PM bit inside FC signals power-save state"},
        {"name": "Duration/ID", "offset_bytes": 2, "length_bytes": 2, "notes": ""},
        {"name": "Address 1", "offset_bytes": 4, "length_bytes": 6, "notes": ""},
        {"name": "Address 2", "offset_bytes": 10, "length_bytes": 6, "notes": ""},
        {"name": "Address 3", "offset_bytes": 16, "length_bytes": 6, "notes": ""},
        {"name": "Sequence Control", "offset_bytes": 22, "length_bytes": 2, "notes": ""},
        {"name": "QoS Control", "offset_bytes": 24, "length_bytes": 2, "notes": ""},
    ],
    "frame-eapol-key": [
        {"name": "LLC/SNAP", "offset_bytes": 0, "length_bytes": 8,
         "notes": "encapsulation atop QoS Data frame — EtherType 0x888E"},
        {"name": "EAPOL Version", "offset_bytes": 8, "length_bytes": 1,
         "notes": "0x02 for 802.1X-2004, 0x03 for 802.1X-2010"},
        {"name": "EAPOL Type", "offset_bytes": 9, "length_bytes": 1,
         "notes": "0x03 for EAPOL-Key"},
        {"name": "EAPOL Length", "offset_bytes": 10, "length_bytes": 2,
         "notes": "length of the Key Descriptor that follows"},
        {"name": "Descriptor Type", "offset_bytes": 12, "length_bytes": 1,
         "notes": "0x02 for RSN"},
        {"name": "Key Information", "offset_bytes": 13, "length_bytes": 2,
         "notes": "type/direction/version/install/ack/mic/secure/error/request/encrypted-key-data/SMK bits"},
        {"name": "Key Length", "offset_bytes": 15, "length_bytes": 2, "notes": ""},
        {"name": "Replay Counter", "offset_bytes": 17, "length_bytes": 8,
         "notes": "monotonic per 4-way message"},
        {"name": "Key Nonce", "offset_bytes": 25, "length_bytes": 32,
         "notes": "ANonce (M1/M3) or SNonce (M2/M4)"},
        {"name": "EAPOL Key IV", "offset_bytes": 57, "length_bytes": 16, "notes": ""},
        {"name": "Key RSC", "offset_bytes": 73, "length_bytes": 8, "notes": ""},
        {"name": "Key ID (Reserved)", "offset_bytes": 81, "length_bytes": 8, "notes": ""},
        {"name": "Key MIC", "offset_bytes": 89, "length_bytes": 16,
         "notes": "MIC over the packet with MIC field zeroed — the hashcat-crackable field"},
        {"name": "Key Data Length", "offset_bytes": 105, "length_bytes": 2, "notes": ""},
        {"name": "Key Data", "offset_bytes": 107, "length_bytes": None,
         "notes": "M1: PMKID KDE (steube-2018 crack surface). M3: GTK KDE + optional IGTK KDE + Lifetime KDE"},
    ],
    # Remaining frames — small structural notes / kept as-is for consistency
    "frame-mgmt-atim": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
         "notes": "type=0, subtype=9; IBSS-only ATIM message"},
    ],
    "frame-mgmt-timing-advertisement": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=0, subtype=6"},
        {"name": "Timestamp / TA fields", "offset_bytes": 24, "length_bytes": None,
         "notes": "802.11v Timing Advertisement per §9.3.3.11"},
    ],
    "frame-mgmt-action-no-ack": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=0, subtype=14"},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": ""},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": ""},
        {"name": "Action Payload", "offset_bytes": 26, "length_bytes": None, "notes": ""},
    ],
    # CF variants — small, mostly historical; provide placeholders.
    "frame-data-cf-ack": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=2, subtype=1"},
    ],
    "frame-data-cf-poll": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=2, subtype=2"},
    ],
    "frame-data-cf-ack-poll": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=2, subtype=3"},
    ],
    "frame-qos-data-cf-ack": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=2, subtype=9"},
    ],
    "frame-qos-data-cf-poll": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": "type=2, subtype=10"},
    ],
    # Action-family variants — payload structure follows §9.6.
    "frame-action-btm-request": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "10 (WNM)"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "7 (BSS Transition Request)"},
        {"name": "Dialog Token", "offset_bytes": 26, "length_bytes": 1, "notes": ""},
        {"name": "Request Mode", "offset_bytes": 27, "length_bytes": 1,
         "notes": "preferred-candidate / abridged / disassoc-imminent / BSS-termination / ESS-disassoc-imminent bits"},
        {"name": "Disassociation Timer", "offset_bytes": 28, "length_bytes": 2, "notes": ""},
        {"name": "Validity Interval", "offset_bytes": 30, "length_bytes": 1, "notes": ""},
        {"name": "Optional Sub-Elements", "offset_bytes": 31, "length_bytes": None,
         "notes": "BSS Termination Duration, Session Info URL, BSS Transition Candidate List (neighbor entries)"},
    ],
    "frame-action-neighbor-report-request": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "5 (Radio Measurement)"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "4 (Neighbor Report Request)"},
        {"name": "Dialog Token", "offset_bytes": 26, "length_bytes": 1, "notes": ""},
        {"name": "Optional SSID subelement", "offset_bytes": 27, "length_bytes": None,
         "notes": "filter by ESS"},
    ],
    "frame-action-neighbor-report-response": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "5"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "5 (Neighbor Report Response)"},
        {"name": "Dialog Token", "offset_bytes": 26, "length_bytes": 1, "notes": ""},
        {"name": "Neighbor Report Elements", "offset_bytes": 27, "length_bytes": None,
         "notes": "list of Neighbor Report Element (IE 52) records — see ies.json"},
    ],
    "frame-action-gas-initial-request": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "4 (Public)"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "10 (GAS Initial Request)"},
        {"name": "Dialog Token", "offset_bytes": 26, "length_bytes": 1, "notes": ""},
        {"name": "Advertisement Protocol Element", "offset_bytes": 27, "length_bytes": None,
         "notes": "IE 108, contains protocol ID (0 = ANQP)"},
        {"name": "Query Length", "offset_bytes": None, "length_bytes": 2, "notes": ""},
        {"name": "Query (ANQP element IDs list)", "offset_bytes": None, "length_bytes": None,
         "notes": "list of ANQP element IDs the STA is requesting"},
    ],
    "frame-action-gas-initial-response": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "4"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "11 (GAS Initial Response)"},
        {"name": "Dialog Token", "offset_bytes": 26, "length_bytes": 1, "notes": ""},
        {"name": "Status Code", "offset_bytes": 27, "length_bytes": 2, "notes": ""},
        {"name": "GAS Comeback Delay", "offset_bytes": 29, "length_bytes": 2, "notes": ""},
        {"name": "Advertisement Protocol Element", "offset_bytes": 31, "length_bytes": None, "notes": ""},
        {"name": "Query Response Length", "offset_bytes": None, "length_bytes": 2, "notes": ""},
        {"name": "Query Response (ANQP elements)", "offset_bytes": None, "length_bytes": None,
         "notes": "concatenated ANQP element payloads"},
    ],
    "frame-action-block-ack-add": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "3 (Block Ack)"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "0=ADDBA Req / 1=ADDBA Resp"},
        {"name": "Dialog Token / Timeout / Parameters", "offset_bytes": 26, "length_bytes": None,
         "notes": "see IEEE 802.11-2020 §9.6.3"},
    ],
    "frame-action-csa-announce": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "0 (Spectrum Mgmt)"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "4 (Channel Switch Announcement)"},
        {"name": "CSA IE", "offset_bytes": 26, "length_bytes": None,
         "notes": "carries IE 37 (see ies.json:ie-channel-switch-announcement)"},
    ],
    "frame-action-ft-request": [
        {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24, "notes": ""},
        {"name": "Category", "offset_bytes": 24, "length_bytes": 1, "notes": "6 (Fast BSS Transition)"},
        {"name": "Action", "offset_bytes": 25, "length_bytes": 1, "notes": "1=FT Request / 2=FT Response"},
        {"name": "STA Address", "offset_bytes": 26, "length_bytes": 6, "notes": "STA to which the FT applies"},
        {"name": "Target AP Address", "offset_bytes": 32, "length_bytes": 6, "notes": ""},
        {"name": "Payload (MDE + FTE + RSNE)", "offset_bytes": 38, "length_bytes": None,
         "notes": "carries the FT Element (IE 55) — see ies.json"},
    ],
}


# ---------------------------------------------------------------------------
# F2 — wctf_uses extension for records that lack a list.
# ---------------------------------------------------------------------------

WCTF_USES: dict[str, list[str]] = {
    "frame-mgmt-probe-response": [
        "hidden-SSID reveal (probe response confirms the SSID that a beacon hid)",
        "AP fingerprint via IE order + timestamp cadence",
    ],
    "frame-mgmt-auth": [
        "SAE Commit/Confirm carries the pairwise key exchange (WPA3)",
        "FT-over-air uses this frame for the initial FT authentication",
    ],
    "frame-mgmt-assoc-request": [
        "client's RSN IE picks cipher+AKM from the AP's advertised set — downgrade opportunity",
        "carries the SNonce indirectly via the 4-way that follows",
    ],
    "frame-mgmt-assoc-response": [
        "Status Code 0 confirms association; anything else lets a WIDS distinguish rogue-farm behavior",
    ],
    "frame-mgmt-reassoc-request": [
        "802.11r roams put the FTE + MDE here — captured for hashcat 22000",
    ],
    "frame-mgmt-deauth": [
        "reason codes 3/7/15 tell a WIDS whether the deauth was intentional or attacker-forged",
    ],
    "frame-mgmt-disassoc": [
        "Kr00k trigger — unicast disassoc against a vulnerable Broadcom/Cypress client leaks the all-zero-PTK tail",
    ],
    "frame-mgmt-action": [
        "BTM Request / Neighbor Report Response / GAS carry roaming + 11u recon primitives",
        "action-frame-based CSA is the CSA-rogue-channel primitive vector",
    ],
    "frame-ctrl-rts": [
        "NAV manipulation — long Duration values silence neighbors",
    ],
    "frame-ctrl-cts": [
        "CTS-to-self silencing DoS — attacker emits CTS with own MAC as RA + long Duration",
    ],
    "frame-ctrl-blockack": [
        "block-ack window manipulation surfaces some driver bugs; useful in WCTF fuzz puzzles",
    ],
    "frame-ctrl-trigger": [
        "OFDMA Trigger frame is the malformed-Trigger DoS vector (ru-based-ofdma-dos)",
    ],
    "frame-ctrl-ps-poll": [
        "power-save queue manipulation → Framing Frames (Vanhoef 2023) primitive",
    ],
    "frame-data-qos-data": [
        "carries encrypted user payload — decrypt with recovered PSK to read the flag",
        "A-MSDU flag confusion is the FragAttacks vector (fragattacks-plaintext-inject)",
    ],
    "frame-eapol-key": [
        "M1 alone leaks PMKID in the Key Data KDE (Steube 2018)",
        "M2 is the load-bearing message for offline PSK crack",
        "M3 keyreinstall triggers KRACK on unpatched clients",
    ],
    "frame-mgmt-reassoc-response": [
        "carries the FTE for 802.11r roams",
    ],
    "frame-action-btm-request": [
        "primary vector for btm-forced-roam",
    ],
    "frame-action-neighbor-report-response": [
        "primary vector for neighbor-report-spoof",
    ],
    "frame-action-gas-initial-request": [
        "primary vector for anqp-realm-enum",
    ],
    "frame-action-gas-initial-response": [
        "AP response carries the ANQP elements — Passpoint realm leak surface",
    ],
    "frame-action-csa-announce": [
        "csa-rogue-channel primitive",
    ],
    "frame-action-ft-request": [
        "carries the FTE for 802.11r roams — hashcat 22000 target",
    ],
    "frame-data": [
        "encrypted payload (CCMP/GCMP) — decrypt path once PSK is recovered",
    ],
    "frame-data-null": [
        "power-save PM-bit signal — Framing Frames abuse target",
    ],
    "frame-qos-null-data": [
        "power-save PM-bit signal (QoS variant) — Framing Frames target",
    ],
}


# ---------------------------------------------------------------------------
# I1 — IE byte layouts. Offsets are BODY offsets (after the 2-byte
# Element ID + Length header) unless the element uses the Extension ID
# (element_id=255) pattern, where the first body byte is the ext ID.
# ---------------------------------------------------------------------------

IE_LAYOUTS: dict[str, list[dict]] = {
    "ie-ssid": [
        {"name": "SSID", "offset_bytes": 0, "length_bytes": None,
         "notes": "0–32 bytes; length 0 = hidden SSID beacon; not NUL-terminated"},
    ],
    "ie-supported-rates": [
        {"name": "Supported Rates", "offset_bytes": 0, "length_bytes": None,
         "notes": "1–8 bytes; each byte = rate in 500 kbps units; high bit = 'basic rate'"},
    ],
    "ie-ds-parameter-set": [
        {"name": "Current Channel", "offset_bytes": 0, "length_bytes": 1,
         "notes": "channel number (1..14 for 2.4 GHz, 36..165 for 5 GHz)"},
    ],
    "ie-tim": [
        {"name": "DTIM Count", "offset_bytes": 0, "length_bytes": 1,
         "notes": "beacons remaining until the next DTIM"},
        {"name": "DTIM Period", "offset_bytes": 1, "length_bytes": 1,
         "notes": "beacons between DTIMs (typically 1..10)"},
        {"name": "Bitmap Control", "offset_bytes": 2, "length_bytes": 1,
         "notes": "bit 0 = broadcast traffic pending; bits 1–7 = bitmap offset"},
        {"name": "Partial Virtual Bitmap", "offset_bytes": 3, "length_bytes": None,
         "notes": "1–251 bytes; each bit = AID with buffered traffic"},
    ],
    "ie-country": [
        {"name": "Country String", "offset_bytes": 0, "length_bytes": 3,
         "notes": "2-char ISO 3166 country code + third char (O=outdoor, I=indoor, ' '=any)"},
        {"name": "Regulatory Triplets", "offset_bytes": 3, "length_bytes": None,
         "notes": "sequence of 3-byte {First Channel, Number of Channels, Max TX Power dBm} triples"},
    ],
    "ie-rsn": [
        {"name": "Version", "offset_bytes": 0, "length_bytes": 2, "notes": "always 0x0001"},
        {"name": "Group Cipher Suite", "offset_bytes": 2, "length_bytes": 4,
         "notes": "OUI (3B: 00-0F-AC) + Suite Type (1B): 1=WEP-40 2=TKIP 4=CCMP-128 5=WEP-104 6=BIP-CMAC-128 8=GCMP-128 9=GCMP-256"},
        {"name": "Pairwise Cipher Suite Count", "offset_bytes": 6, "length_bytes": 2, "notes": ""},
        {"name": "Pairwise Cipher Suite List", "offset_bytes": 8, "length_bytes": None,
         "notes": "N × 4 bytes (OUI + Suite Type)"},
        {"name": "AKM Suite Count", "offset_bytes": None, "length_bytes": 2, "notes": "offset depends on pairwise count"},
        {"name": "AKM Suite List", "offset_bytes": None, "length_bytes": None,
         "notes": "N × 4 bytes: 1=802.1X, 2=PSK, 3=FT-802.1X, 4=FT-PSK, 5=802.1X-SHA256, 6=PSK-SHA256, 8=SAE, 9=FT-SAE, 11=Suite B 192, 12=OWE, 18=SAE-EXT-KEY (H2E)"},
        {"name": "RSN Capabilities", "offset_bytes": None, "length_bytes": 2,
         "notes": "MFPR/MFPC (bits 6/7), PeerKey / SPP-A-MSDU / …"},
        {"name": "PMKID Count", "offset_bytes": None, "length_bytes": 2, "notes": "may be absent"},
        {"name": "PMKID List", "offset_bytes": None, "length_bytes": None,
         "notes": "N × 16 bytes; M1 with a PMKID here is the Steube-2018 crack path"},
        {"name": "Group Management Cipher Suite", "offset_bytes": None, "length_bytes": 4,
         "notes": "PMF group cipher — BIP-CMAC-128 by default"},
    ],
    "ie-wps": [
        {"name": "Vendor OUI", "offset_bytes": 0, "length_bytes": 3, "notes": "00-50-F2 (Microsoft)"},
        {"name": "OUI Type", "offset_bytes": 3, "length_bytes": 1, "notes": "0x04 (WPS)"},
        {"name": "WPS Attribute List", "offset_bytes": 4, "length_bytes": None,
         "notes": "sequence of TLVs: Manufacturer (0x1021), Model Name (0x1023), Model Number (0x1024), Serial Number (0x1042), Primary Device Type (0x1054), Config Methods (0x1008), WPS State (0x1044), AP Setup Locked (0x1057), Version (0x104A)"},
    ],
    "ie-vendor-specific": [
        {"name": "Vendor OUI", "offset_bytes": 0, "length_bytes": 3,
         "notes": "identifies the vendor (00-50-F2 Microsoft, 00-90-4C Broadcom, 00-40-96 Cisco)"},
        {"name": "OUI Type", "offset_bytes": 3, "length_bytes": 1,
         "notes": "vendor-defined subtype (WPA=1 for OUI 00-50-F2, WPS=4, WMM=2)"},
        {"name": "Vendor-Defined Body", "offset_bytes": 4, "length_bytes": None,
         "notes": "opaque per vendor; primary beacon-stego channel"},
    ],
    "ie-mobility-domain": [
        {"name": "Mobility Domain ID", "offset_bytes": 0, "length_bytes": 2,
         "notes": "identifies the FT roaming group"},
        {"name": "FT Capability + Policy", "offset_bytes": 2, "length_bytes": 1,
         "notes": "bit 0 = Fast BSS Transition Over DS; bit 1 = Resource Request Protocol Capability"},
    ],
    "ie-fast-bss-transition": [
        {"name": "MIC Control", "offset_bytes": 0, "length_bytes": 2,
         "notes": "IE Count byte + reserved"},
        {"name": "MIC", "offset_bytes": 2, "length_bytes": 16,
         "notes": "MIC over the FT reassoc"},
        {"name": "ANonce", "offset_bytes": 18, "length_bytes": 32, "notes": ""},
        {"name": "SNonce", "offset_bytes": 50, "length_bytes": 32, "notes": ""},
        {"name": "Optional Parameters", "offset_bytes": 82, "length_bytes": None,
         "notes": "R1KH-ID, GTK, IGTK, R0KH-ID sub-elements"},
    ],
    "ie-interworking": [
        {"name": "Access Network Options", "offset_bytes": 0, "length_bytes": 1,
         "notes": "Access Network Type (4 bits): 0=Private, 1=Private w/ guest, 2=Chargeable public, 3=Free public, 15=Test; Internet bit; ASRA bit; ESR bit; UESA bit"},
        {"name": "Venue Info", "offset_bytes": 1, "length_bytes": 2,
         "notes": "Group + Type — optional; present when Venue subfield bit set"},
        {"name": "HESSID", "offset_bytes": 3, "length_bytes": 6,
         "notes": "Homogeneous ESSID — optional MAC-formatted identifier"},
    ],
    "ie-roaming-consortium": [
        {"name": "Number of ANQP OIs", "offset_bytes": 0, "length_bytes": 1, "notes": ""},
        {"name": "OI Lengths", "offset_bytes": 1, "length_bytes": 1,
         "notes": "high nibble: OI 1 length; low nibble: OI 2 length"},
        {"name": "OI 1", "offset_bytes": 2, "length_bytes": None,
         "notes": "3-15 bytes — the Roaming Consortium OI to auto-associate"},
        {"name": "OI 2 (optional)", "offset_bytes": None, "length_bytes": None, "notes": ""},
        {"name": "OI 3 (optional)", "offset_bytes": None, "length_bytes": None, "notes": ""},
    ],
    "ie-rnr": [
        {"name": "TBTT Information Field(s)", "offset_bytes": 0, "length_bytes": None,
         "notes": "list of {TBTT Info Header, Operating Class, Channel Number, TBTT Info Set}"},
        {"name": "TBTT Info Header", "offset_bytes": 0, "length_bytes": 2,
         "notes": "TBTT Info Field Type, Filtered Neighbor AP bit, TBTT Info Count, TBTT Info Length"},
        {"name": "Operating Class", "offset_bytes": 2, "length_bytes": 1, "notes": ""},
        {"name": "Channel Number", "offset_bytes": 3, "length_bytes": 1,
         "notes": "the 6 GHz channel — enumerable without a 6 GHz radio"},
        {"name": "TBTT Information Set", "offset_bytes": 4, "length_bytes": None,
         "notes": "per-AP BSSID + Short SSID + BSS Parameters"},
    ],
    "ie-mld-basic": [
        {"name": "Element ID Extension", "offset_bytes": 0, "length_bytes": 1,
         "notes": "0x6B (107) = Basic Multi-Link"},
        {"name": "Multi-Link Control", "offset_bytes": 1, "length_bytes": 2,
         "notes": "Type + Presence Bitmap"},
        {"name": "Common Info", "offset_bytes": 3, "length_bytes": None,
         "notes": "MLD MAC (6 B), Link ID Info, BSS Parameters Change Count, Medium Sync Delay Info, EML Capabilities, MLD Capabilities and Operations"},
        {"name": "Per-STA Profile Sub-Elements", "offset_bytes": None, "length_bytes": None,
         "notes": "per-link setup info (STA MAC, Link ID, per-link capabilities)"},
    ],
    "ie-extended-capabilities": [
        {"name": "Extended Capabilities Bitmap", "offset_bytes": 0, "length_bytes": None,
         "notes": "1..N bytes; bit 0 = 2040 BSS Coex Mgmt Support; bit 22 = TDLS; bit 24 = TDLS Prohibited; bit 30 = Interworking (11u); bit 31 = QoS Map; bit 33 = TDLS Peer PSM Sup; bit 46 = WNM Sleep Mode; bit 51 = Operating Mode Notification (11ac); bit 62 = TWT Requester"},
    ],
    "ie-erp-info": [
        {"name": "ERP Information", "offset_bytes": 0, "length_bytes": 1,
         "notes": "bit 0 NonERP_Present; bit 1 Use_Protection; bit 2 Barker_Preamble_Mode"},
    ],
    "ie-channel-switch-announcement": [
        {"name": "Channel Switch Mode", "offset_bytes": 0, "length_bytes": 1,
         "notes": "0 = no restriction on Tx before switch; 1 = STA must stop Tx until switch"},
        {"name": "New Channel Number", "offset_bytes": 1, "length_bytes": 1, "notes": ""},
        {"name": "Channel Switch Count", "offset_bytes": 2, "length_bytes": 1,
         "notes": "beacons until switch (0 = immediate)"},
    ],
    "ie-rsnxe": [
        {"name": "Extension Capabilities Bitmap", "offset_bytes": 0, "length_bytes": None,
         "notes": "bit 0 = Field Length; bit 4 = Protected TWT Operations Support; bit 5 = SAE Hash-to-Element; bit 6 = SAE PK Only"},
    ],
    "ie-ht-capabilities": [
        {"name": "HT Capabilities Info", "offset_bytes": 0, "length_bytes": 2,
         "notes": "LDPC, Supported Channel Width Set, SM Power Save, HT Greenfield, Short GI 20/40, TX/RX STBC, HT Delayed Block Ack, MaxA-MSDU, DSSS-CCK Mode 40 MHz, LSIG TXOP Protection"},
        {"name": "A-MPDU Parameters", "offset_bytes": 2, "length_bytes": 1, "notes": ""},
        {"name": "Supported MCS Set", "offset_bytes": 3, "length_bytes": 16,
         "notes": "16-byte bitmap of supported MCS indices — strong device fingerprint"},
        {"name": "HT Extended Capabilities", "offset_bytes": 19, "length_bytes": 2, "notes": ""},
        {"name": "TX Beamforming Capabilities", "offset_bytes": 21, "length_bytes": 4, "notes": ""},
        {"name": "ASEL Capabilities", "offset_bytes": 25, "length_bytes": 1, "notes": ""},
    ],
    "ie-vht-capabilities": [
        {"name": "VHT Capabilities Info", "offset_bytes": 0, "length_bytes": 4,
         "notes": "Max MPDU Length, Supported Channel Width Set, RX LDPC, Short GI 80/160, TX/RX STBC, SU/MU Beamformer/Beamformee, MU MPDU Length Exponent, VHT TXOP PS"},
        {"name": "Supported VHT-MCS and NSS Set", "offset_bytes": 4, "length_bytes": 8, "notes": ""},
    ],
    "ie-he-capabilities": [
        {"name": "Element ID Extension", "offset_bytes": 0, "length_bytes": 1, "notes": "0x23 (35) = HE Capabilities"},
        {"name": "HE MAC Capabilities Info", "offset_bytes": 1, "length_bytes": 6, "notes": ""},
        {"name": "HE PHY Capabilities Info", "offset_bytes": 7, "length_bytes": 11, "notes": ""},
        {"name": "Supported HE-MCS and NSS Set", "offset_bytes": 18, "length_bytes": None,
         "notes": "variable — 4/8/12 bytes based on max NSS + BW combinations"},
    ],
    "ie-eht-capabilities": [
        {"name": "Element ID Extension", "offset_bytes": 0, "length_bytes": 1, "notes": "0x6C (108) = EHT Capabilities"},
        {"name": "EHT MAC Capabilities Info", "offset_bytes": 1, "length_bytes": 2, "notes": ""},
        {"name": "EHT PHY Capabilities Info", "offset_bytes": 3, "length_bytes": 9, "notes": ""},
        {"name": "Supported EHT-MCS and NSS Set", "offset_bytes": 12, "length_bytes": None, "notes": ""},
    ],
    "ie-owe-diffie-hellman": [
        {"name": "Element ID Extension", "offset_bytes": 0, "length_bytes": 1, "notes": "0x20 (32) = OWE DH"},
        {"name": "Group", "offset_bytes": 1, "length_bytes": 2, "notes": "ECDH group ID (19 = P-256)"},
        {"name": "Public Key", "offset_bytes": 3, "length_bytes": None, "notes": "compressed ECDH public key"},
    ],
    "ie-oci": [
        {"name": "Element ID Extension", "offset_bytes": 0, "length_bytes": 1, "notes": "0x36 (54) = OCI"},
        {"name": "Operating Class", "offset_bytes": 1, "length_bytes": 1, "notes": ""},
        {"name": "Primary Channel Number", "offset_bytes": 2, "length_bytes": 1, "notes": ""},
        {"name": "Frequency Segment 1 Channel Number", "offset_bytes": 3, "length_bytes": 1, "notes": ""},
    ],
    "ie-6ghz-operation": [
        {"name": "Element ID Extension", "offset_bytes": 0, "length_bytes": 1, "notes": "0x3B (59) = 6 GHz Operation"},
        {"name": "Primary Channel Number", "offset_bytes": 1, "length_bytes": 1, "notes": ""},
        {"name": "Control", "offset_bytes": 2, "length_bytes": 1,
         "notes": "Channel Width, Duplicate Beacon, Regulatory Info bits"},
        {"name": "Channel Center Frequency Segment 0", "offset_bytes": 3, "length_bytes": 1, "notes": ""},
        {"name": "Channel Center Frequency Segment 1", "offset_bytes": 4, "length_bytes": 1, "notes": ""},
        {"name": "Minimum Rate", "offset_bytes": 5, "length_bytes": 1, "notes": ""},
    ],
    "ie-twt": [
        {"name": "Element ID Extension", "offset_bytes": 0, "length_bytes": 1, "notes": "0x4E (78) = TWT"},
        {"name": "Control", "offset_bytes": 1, "length_bytes": 1,
         "notes": "NDP Paging Indicator, Responder PM Mode, Negotiation Type"},
        {"name": "TWT Parameters", "offset_bytes": 2, "length_bytes": None,
         "notes": "Target Wake Time (8 B), Nominal Minimum TWT Wake Duration (1 B), TWT Wake Interval Mantissa (2 B), TWT Wake Interval Exponent (5 bits) — encoded per §9.4.2.199"},
    ],
    "ie-transition-disable": [
        {"name": "KDE Type", "offset_bytes": 0, "length_bytes": 4,
         "notes": "WFA-defined OUI 50:6F:9A + Data Type 0x20 (Transition Disable) — delivered in EAPOL-Key M3 Key Data"},
        {"name": "Transition Disable Bitmap", "offset_bytes": 4, "length_bytes": None,
         "notes": "bit 0 = WPA3 Personal; bit 1 = SAE-PK; bit 2 = WPA3 Enterprise; bit 3 = Enhanced Open (OWE)"},
    ],
    "ie-supported-mcs-set": [
        {"name": "Supported MCS Set", "offset_bytes": 0, "length_bytes": 16,
         "notes": "sub-field inside IE 45; 16-byte bitmap of supported MCS indices"},
    ],
    "ie-neighbor-report": [
        {"name": "BSSID", "offset_bytes": 0, "length_bytes": 6, "notes": ""},
        {"name": "BSSID Info", "offset_bytes": 6, "length_bytes": 4,
         "notes": "AP Reachability, Security, Key Scope, Capability bits"},
        {"name": "Operating Class", "offset_bytes": 10, "length_bytes": 1, "notes": ""},
        {"name": "Channel Number", "offset_bytes": 11, "length_bytes": 1, "notes": ""},
        {"name": "PHY Type", "offset_bytes": 12, "length_bytes": 1, "notes": ""},
        {"name": "Optional Sub-Elements", "offset_bytes": 13, "length_bytes": None, "notes": ""},
    ],
    "ie-extended-supported-rates": [
        {"name": "Extended Supported Rates", "offset_bytes": 0, "length_bytes": None,
         "notes": "1..255 bytes; format identical to IE 1 — used when IE 1 overflows 8 rates"},
    ],
    "ie-management-mic": [
        {"name": "Key ID", "offset_bytes": 0, "length_bytes": 2, "notes": ""},
        {"name": "IPN (IGTK Packet Number)", "offset_bytes": 2, "length_bytes": 6, "notes": ""},
        {"name": "MIC", "offset_bytes": 8, "length_bytes": 8,
         "notes": "8-byte MIC by default (BIP-CMAC-128); 16 for BIP-GMAC-256"},
    ],
}


# All other IEs get an opaque placeholder — schema uniform, but signals
# we haven't decoded that IE at the byte level yet.
_OPAQUE = [{"name": "opaque", "offset_bytes": 0, "length_bytes": None,
            "notes": "see IEEE 802.11-2020 §9.4"}]


# ---------------------------------------------------------------------------
# I2 — ANQP element records. The plan's ontology lists ANQP under
# information_element; the corpus has no direct ANQP-element records.
# ---------------------------------------------------------------------------

ANQP_RECORDS: list[dict] = [
    {
        "id": "ie-anqp-nai-realm",
        "name": "ANQP NAI Realm List (ANQP element 268)",
        "aliases": ["nai-realm"],
        "category": "information_element",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["ie-interworking", "std-802-11u", "anqp-realm-enum"],
        "technical_body": {
            "anqp_element_id": 268,
            "spec": "802.11u §9.4.5.10",
            "layout": [
                {"name": "NAI Realm Count", "offset_bytes": 0, "length_bytes": 2, "notes": ""},
                {"name": "NAI Realm Entries", "offset_bytes": 2, "length_bytes": None,
                 "notes": "list of {Length, Encoding, NAI Realm Length, NAI Realm, EAP Method Count, EAP Method List}"},
            ],
            "wctf_uses": ["enterprise realm string leaks the target org's domain (@corp.example) before any auth exchange"],
        },
    },
    {
        "id": "ie-anqp-roaming-consortium",
        "name": "ANQP Roaming Consortium List (ANQP element 264)",
        "category": "information_element",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["ie-roaming-consortium", "passpoint-roaming-consortium-spoof"],
        "technical_body": {
            "anqp_element_id": 264,
            "spec": "802.11u §9.4.5.6",
            "layout": [
                {"name": "OI Duples", "offset_bytes": 0, "length_bytes": None,
                 "notes": "list of {OI Length, OI (3..15 bytes)}"},
            ],
            "wctf_uses": ["Passpoint clients auto-associate to any AP advertising a matching Roaming Consortium OI"],
        },
    },
    {
        "id": "ie-anqp-venue-info",
        "name": "ANQP Venue Name (ANQP element 262)",
        "category": "information_element",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["ie-interworking"],
        "technical_body": {
            "anqp_element_id": 262,
            "spec": "802.11u §9.4.5.4",
            "layout": [
                {"name": "Venue Group", "offset_bytes": 0, "length_bytes": 1, "notes": ""},
                {"name": "Venue Type", "offset_bytes": 1, "length_bytes": 1, "notes": ""},
                {"name": "Venue Name Duples", "offset_bytes": 2, "length_bytes": None,
                 "notes": "list of {Length, Language Code (3 B), Venue Name (UTF-8)}"},
            ],
            "wctf_uses": ["WCTF flag lives in the Venue Name string on some Passpoint puzzles"],
        },
    },
    {
        "id": "ie-anqp-3gpp-network",
        "name": "ANQP 3GPP Cellular Network (ANQP element 267)",
        "category": "information_element",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["ie-interworking"],
        "technical_body": {
            "anqp_element_id": 267,
            "spec": "802.11u §9.4.5.9",
            "layout": [
                {"name": "GUD Version", "offset_bytes": 0, "length_bytes": 1, "notes": ""},
                {"name": "User Data Length", "offset_bytes": 1, "length_bytes": 1, "notes": ""},
                {"name": "PLMN List", "offset_bytes": 2, "length_bytes": None,
                 "notes": "list of MCC+MNC pairs advertising cellular offload"},
            ],
            "wctf_uses": ["carrier Wi-Fi offload — the PLMN list leaks which cellular networks the AP will accept"],
        },
    },
    {
        "id": "ie-anqp-domain-name",
        "name": "ANQP Domain Name List (ANQP element 271)",
        "category": "information_element",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["ie-interworking"],
        "technical_body": {
            "anqp_element_id": 271,
            "spec": "802.11u §9.4.5.13",
            "layout": [
                {"name": "Domain Name Duples", "offset_bytes": 0, "length_bytes": None,
                 "notes": "list of {Length, Domain Name (UTF-8, e.g. 'example.com')}"},
            ],
            "wctf_uses": ["operator/venue domain revealed pre-association — useful for phishing-page brand match"],
        },
    },
    {
        "id": "ie-anqp-osu-providers",
        "name": "ANQP OSU Providers List (Hotspot 2.0)",
        "category": "information_element",
        "region": "universal",
        "era_bounds": ["2013", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["ie-interworking", "anqp-realm-enum"],
        "technical_body": {
            "anqp_vendor_specific": True,
            "spec": "Hotspot 2.0 OSU Providers List — vendor-specific ANQP-VS OUI 50:6F:9A subtype 0x0B",
            "layout": [
                {"name": "OSU SSID", "offset_bytes": 0, "length_bytes": None, "notes": "friendly name of the OSU SSID"},
                {"name": "OSU Providers", "offset_bytes": None, "length_bytes": None,
                 "notes": "list of {URI, Friendly Name, Icons, Server-cert Hash}"},
            ],
            "wctf_uses": ["OSU URI often contains attacker-plantable stego on rogue Passpoint APs"],
        },
    },
]


# I3 — alias additions on existing IE records
IE_ALIAS_ADDITIONS: dict[str, list[str]] = {
    "ie-mobility-domain": ["ie-mde"],
    "ie-interworking": ["ie-anqp"],
}


# ---------------------------------------------------------------------------
# core pass
# ---------------------------------------------------------------------------


def apply_frames(records: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in records}

    for rid, layout in FRAME_LAYOUTS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        tb = rec.setdefault("technical_body", {})
        if not tb.get("fields"):
            tb["fields"] = layout

    for rid, uses in WCTF_USES.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        tb = rec.setdefault("technical_body", {})
        if not tb.get("wctf_uses"):
            tb["wctf_uses"] = uses

    # Every remaining frame record without a fields[] gets a MAC-header
    # placeholder so lookup_frame returns a uniform shape.
    for r in records:
        tb = r.setdefault("technical_body", {})
        if not tb.get("fields"):
            tb["fields"] = [
                {"name": "MAC Header", "offset_bytes": 0, "length_bytes": 24,
                 "notes": f"type={tb.get('frame_type', '?')}, subtype={tb.get('subtype', '?')}; "
                          "see IEEE 802.11-2020 §9"},
            ]

    return records


def apply_ies(records: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in records}

    for rid, layout in IE_LAYOUTS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        tb = rec.setdefault("technical_body", {})
        if not tb.get("layout"):
            tb["layout"] = layout

    # Everything else gets an opaque placeholder.
    for r in records:
        tb = r.setdefault("technical_body", {})
        if not tb.get("layout"):
            tb["layout"] = _OPAQUE

    # I3 aliases
    for rid, extras in IE_ALIAS_ADDITIONS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        current = list(rec.get("aliases") or [])
        for a in extras:
            if a not in current:
                current.append(a)
        rec["aliases"] = current

    # I2 — new ANQP records (skip if already present, idempotent).
    existing = {r["id"] for r in records}
    for new in ANQP_RECORDS:
        if new["id"] not in existing:
            records.append(new)

    return records


def main() -> int:
    frames = json.loads(FRAMES.read_text(encoding="utf-8"))
    frames = apply_frames(frames)
    FRAMES.write_text(json.dumps(frames, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"depth-pass-frames-ies: wrote {FRAMES} — {len(frames)} records", file=sys.stderr)

    ies = json.loads(IES.read_text(encoding="utf-8"))
    ies = apply_ies(ies)
    IES.write_text(json.dumps(ies, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"depth-pass-frames-ies: wrote {IES} — {len(ies)} records", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
