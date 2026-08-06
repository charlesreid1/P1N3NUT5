"""
SSH command executor against the Pineapple Mark VII OpenWRT userland.

Phase 0 stub. Will hold:

  * key- or password-auth (`PINEAPPLE_SSH_KEY` / `PINEAPPLE_SSH_PASSWORD`)
  * async command execution (asyncssh) for concurrent `tail -f`,
    `airodump-ng`, and long-running `hcxdumptool` sessions
  * an SCP channel for pcap ingest and hostapd.conf upload
  * per-invocation `call_log` capture — every shell command recorded
    verbatim with timing, stdout/stderr, and exit code

Best for capabilities the WebUI does not expose: raw frame capture,
frame injection, 4-way handshake capture, PMKID capture, manual
hostapd for rogue APs, file transfer, log tailing, kernel/mac80211
tuning. See "The transport split — API vs SSH" in plan-organize.md.
"""

from __future__ import annotations
