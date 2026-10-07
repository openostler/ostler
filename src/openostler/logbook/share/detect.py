# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Detectors the share scrubber and the verifier run over every file (trip-sharing spec
§8.3 and R14).

- **VIN pattern (R3).** A window of 17 characters from ``[A-HJ-NPR-Z0-9]`` holding at least
  3 digits and 3 letters, or the vehicle's own WMI (when the owner's device knows it)
  followed by 14 VIN characters. Upper case only: a VIN is never written in lower case,
  and the bundle's own hashes and ids are lower-case hex. A match **blocks** a share; it is
  never cut silently.
- **Network identity (R14).** MAC addresses, IPv4 and IPv6 addresses, certificate
  fingerprints, bearer tokens and JWTs, PEM blocks, Ed25519 keys and Tailscale names, by
  pattern; SSIDs, host names, tokens and keys by declared JSON key
  (:data:`NETWORK_KEYS`). :func:`redact_text` and :func:`redact_json` replace them with
  ``**REDACTED**``; :func:`network_hits` finds them.

Pure stdlib.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Iterator, List, Tuple

from ...node.identity import iter_runs

REDACTED = "**REDACTED**"
VIN_LEN = 17
_LETTERS = b"ABCDEFGHJKLMNPRSTUVWXYZ"
_DIGITS = b"0123456789"
VIN_ALPHABET = frozenset(_LETTERS + _DIGITS)


def find_vins(data: "bytes | str", wmi: "str | None" = None) -> "List[int]":
    """Offsets of VIN-pattern matches in ``data`` (one per run of VIN characters: the first
    window that matches)."""
    if isinstance(data, str):
        data = data.encode("latin-1", "replace")
    w = wmi.upper().encode("ascii", "ignore") if wmi else b""
    out: "List[int]" = []
    for off, run in iter_runs(data, VIN_ALPHABET, VIN_LEN):
        for i in range(len(run) - VIN_LEN + 1):
            win = run[i:i + VIN_LEN]
            digits = sum(1 for b in win if b in _DIGITS)
            if (digits >= 3 and VIN_LEN - digits >= 3) or (w and win.startswith(w)):
                out.append(off + i)
                break
    return out


# ---- network identity (R14) ----------------------------------------------------------- #
_HEX2 = r"[0-9A-Fa-f]{2}"
_NETWORK_PATTERNS: "Tuple[Tuple[str, re.Pattern], ...]" = (
    ("certificate fingerprint", re.compile(rf"\b(?:{_HEX2}:){{15,}}{_HEX2}\b")),
    ("certificate fingerprint", re.compile(r"\bSHA256:[A-Za-z0-9+/]{43}=?")),
    ("MAC address", re.compile(rf"\b{_HEX2}([:-])(?:{_HEX2}\1){{4}}{_HEX2}\b")),
    ("IPv4 address", re.compile(r"(?<![\w.])(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
                                r"(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}(?![\w.])")),
    ("IPv6 address", re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}(?![\w:])")),
    ("IPv6 address", re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{1,4}:){1,6}:"
                                r"(?:[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4}){0,5})?(?![\w:])")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*")),
    ("PEM block", re.compile(r"-----BEGIN [A-Z0-9 ]+-----")),
    ("peer key", re.compile(r"(?i)\bed25519[:-]?[A-Za-z0-9+/]{40,}={0,2}")),
    ("Tailscale name", re.compile(r"(?i)\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.ts\.net\b")),
)

# JSON keys whose values are network identity or secrets wherever they appear (declared
# keys, R14). Matching is case-insensitive on the whole key.
NETWORK_KEYS = frozenset({
    "mac", "mac_address", "bssid", "ssid", "wifi_ssid", "ip", "ip_address", "ipv4", "ipv6",
    "host", "hostname", "tailscale", "tailscale_name", "tailnet", "token", "bearer",
    "access_token", "refresh_token", "api_key", "apikey", "password", "passphrase", "psk",
    "secret", "fingerprint", "cert_fingerprint", "certificate_fingerprint", "peer_key",
    "public_key", "private_key", "relay_id", "hub_id",
})


def network_hits(text: str) -> "List[Tuple[str, int]]":
    """``(kind, offset)`` for every network-identity pattern in ``text``."""
    out: "List[Tuple[str, int]]" = []
    for kind, rx in _NETWORK_PATTERNS:
        for m in rx.finditer(text):
            out.append((kind, m.start()))
    return sorted(out, key=lambda h: h[1])


def redact_text(text: str) -> "Tuple[str, int]":
    """``text`` with every network-identity pattern replaced; and the count."""
    n = 0
    for _kind, rx in _NETWORK_PATTERNS:
        text, k = rx.subn(REDACTED, text)
        n += k
    return text, n


def _declared(key: Any) -> bool:
    return isinstance(key, str) and key.strip().lower() in NETWORK_KEYS


def redact_json(obj: Any) -> "Tuple[Any, int]":
    """A JSON value with declared keys' values and pattern hits replaced; and the count."""
    if isinstance(obj, dict):
        out, n = {}, 0
        for k, v in obj.items():
            if _declared(k) and v not in (None, REDACTED):
                out[k] = REDACTED
                n += 1
            else:
                out[k], c = redact_json(v)
                n += c
        return out, n
    if isinstance(obj, list):
        items = [redact_json(v) for v in obj]
        return [v for v, _ in items], sum(c for _, c in items)
    if isinstance(obj, str):
        return redact_text(obj)
    return obj, 0


def json_declared_hits(obj: Any, path: str = "") -> "Iterator[str]":
    """JSON paths where a declared network key holds a value that is not redacted."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            if _declared(k) and v not in (None, REDACTED):
                yield p
            else:
                yield from json_declared_hits(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from json_declared_hits(v, f"{path}[{i}]")


def json_strings(obj: Any, path: str = "") -> "Iterator[Tuple[str, str]]":
    """``(path, text)`` for every string key and value of a JSON document."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            yield p, str(k)
            yield from json_strings(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from json_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def ascii_windows(chunks: "Iterable[bytes]") -> "Iterator[Tuple[int, int]]":
    """``(chunk index, offset)`` of VIN matches in each binary chunk."""
    for i, c in enumerate(chunks):
        for off in find_vins(c):
            yield i, off


__all__ = ["NETWORK_KEYS", "REDACTED", "VIN_ALPHABET", "ascii_windows", "find_vins",
           "json_declared_hits", "json_strings", "network_hits", "redact_json",
           "redact_text"]
