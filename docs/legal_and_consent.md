# legal_and_consent

Every P1N3NUT5 tool that transmits (deauth, capture, rogue AP, evil
twin, beacon flood, packet inject) refuses to run without explicit
airspace authorization. Refusal is loud: the tool returns the normal
envelope with `ok=False`, a warning citing this file, and the
`AuthorizationRequired` exception name in the message.

This is not about hedging. At a DEF CON WCTF you flip the flag once
for the session; in an office lab you set an explicit allowlist.
Transmitting on someone else's airspace without either is illegal in
most jurisdictions.

## The `--i-own-the-airspace` flag

The per-session confirm flag. Set it once when the session belongs to
sanctioned airspace (DEF CON's Wireless Village, a lab you own, a
range on a contract).

In an MCP tool call this shows up as `i_own_the_airspace=True` on
every transmitting tool (`do_deauth`, `do_capture_handshake`,
`do_create_rogue_ap`, `do_evil_twin`, `run_sequence`). In a
`run_sequence` call the flag is set once at the top of the call and
applies to every step:

```python
await run_sequence(
    steps=[…],
    i_own_the_airspace=True,   # DEF CON WCTF; one flag for all steps
)
```

## Per-session `authorization`

Office / lab / contract engagements: don't use the airspace flag.
Set an explicit scope with `Authorization` from
[`attacks.py`](../src/p1n3nut5_mcp/attacks.py):

```python
from p1n3nut5_mcp.attacks import Authorization

authz = Authorization(
    ssid_allowlist=("target-lab-2G", "target-lab-5G"),
    bssid_allowlist=("aa:bb:cc:dd:ee:ff",),
)
```

`Authorization` is a `dataclass` with three fields:

- `i_own_the_airspace: bool = False` — the DEF CON flag
- `ssid_allowlist: tuple[str, ...] = ()`
- `bssid_allowlist: tuple[str, ...] = ()`

`allows_target(ssid=?, bssid=?)` returns `True` if
`i_own_the_airspace` is set OR the target matches the allowlist.
The allowlist match is exact on SSID; BSSID is compared
case-insensitively.

## Refusal shape

Every transmitting primitive in `attacks.py` calls `_require_authz`
before it does anything on the wire. Two failure modes:

- **No `authorization` passed.** Raises `AuthorizationRequired` with
  a message that points at this file.
- **`authorization` passed but the target isn't in scope.** Raises
  `AuthorizationRequired` with `target ssid=… bssid=… not in
  authorized scope`.

The server-layer wrappers (`do_deauth`, etc.) construct the
`Authorization` object from `i_own_the_airspace` and pass it down —
`i_own_the_airspace=False` and no allowlist means every transmit
refuses.

## DEF CON WCTF vs office lab

**DEF CON WCTF.** Wireless Village sanctioned airspace. Flag once:
`i_own_the_airspace=True`. Every transmit is a puzzle target that
the village *built* to be attacked. No per-SSID allowlist needed;
that's the point of a village.

**Office lab.** You own the room, you own the target BSSID, but the
neighboring cubicle does not. Use the allowlist. `Authorization`
gates each target individually: if a stray "Starbucks" BSSID shows
up in `list_aps` and someone accidentally puts it in a `do_deauth`
call, the allowlist refuses and the target's off the hook.

Never mix modes in one session. If the room is public airspace,
neither the flag nor the allowlist grants consent — nobody owns the
room, so nobody's decision is yours to make.
