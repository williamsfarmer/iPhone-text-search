"""
Shared helpers for the iMessage search tool.

Everything here is standard-library only (no pip installs) so the tool runs on a
stock Windows 11 Python without extra setup. The two hard parts live here:

  * finding the local iPhone backup and locating a file inside it, and
  * turning Apple's `attributedBody` blob back into plain text (modern iOS stores
    the message body there instead of the `text` column).
"""

from __future__ import annotations

import hashlib
import os
import plistlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Apple's reference date: 2001-01-01 00:00:00 UTC, as a Unix timestamp.
APPLE_EPOCH = 978307200

# Where the Apple Devices app (Microsoft Store) and classic iTunes each keep
# their local backups on Windows.
BACKUP_ROOTS = [
    Path(os.path.expandvars(r"%USERPROFILE%\Apple\MobileSync\Backup")),
    Path(os.path.expandvars(r"%APPDATA%\Apple Computer\MobileSync\Backup")),
]


@dataclass
class Backup:
    path: Path
    device: str
    last_backup: str  # ISO date or "?"
    encrypted: bool

    def label(self) -> str:
        lock = " [ENCRYPTED]" if self.encrypted else ""
        return f"{self.device}  (last backup {self.last_backup}){lock}\n    {self.path}"


def find_backups() -> list[Backup]:
    """Return every iPhone/iPad backup found in the known Windows locations,
    newest first."""
    found: list[Backup] = []
    for root in BACKUP_ROOTS:
        if not root.is_dir():
            continue
        for entry in root.iterdir():
            info = entry / "Info.plist"
            manifest = entry / "Manifest.plist"
            if not manifest.is_file():
                continue
            device, last, encrypted = "Unknown device", "?", False
            try:
                with open(manifest, "rb") as fh:
                    m = plistlib.load(fh)
                encrypted = bool(m.get("IsEncrypted", False))
                last_dt = m.get("Date")
                if isinstance(last_dt, datetime):
                    last = last_dt.date().isoformat()
            except Exception:
                pass
            if info.is_file():
                try:
                    with open(info, "rb") as fh:
                        i = plistlib.load(fh)
                    device = i.get("Device Name") or i.get("Product Name") or device
                    if i.get("Last Backup Date") and last == "?":
                        last = i["Last Backup Date"].date().isoformat()
                except Exception:
                    pass
            found.append(Backup(entry, device, last, encrypted))
    found.sort(key=lambda b: b.last_backup, reverse=True)
    return found


def manifest_hash(domain: str, relative_path: str) -> str:
    """The on-disk filename for a file inside a backup is the SHA-1 of
    'domain-relativePath'."""
    return hashlib.sha1(f"{domain}-{relative_path}".encode("utf-8")).hexdigest()


def locate_in_backup(backup: Path, domain: str, relative_path: str) -> Path | None:
    """Resolve a logical backup file (domain + path) to its real location on disk.

    Prefers Manifest.db (iOS 10+, files live in 2-char subfolders) and falls back
    to the flat legacy layout.
    """
    file_id = manifest_hash(domain, relative_path)
    # iOS 10+ : <backup>/<xx>/<fileID>
    candidate = backup / file_id[:2] / file_id
    if candidate.is_file():
        return candidate
    # Legacy flat layout: <backup>/<fileID>
    candidate = backup / file_id
    if candidate.is_file():
        return candidate
    # Manifest.db is authoritative if the hash guess missed.
    mdb = backup / "Manifest.db"
    if mdb.is_file():
        try:
            con = sqlite3.connect(f"file:{mdb}?mode=ro", uri=True)
            row = con.execute(
                "SELECT fileID FROM Files WHERE domain=? AND relativePath=?",
                (domain, relative_path),
            ).fetchone()
            con.close()
            if row:
                fid = row[0]
                for c in (backup / fid[:2] / fid, backup / fid):
                    if c.is_file():
                        return c
        except Exception:
            pass
    return None


def apple_time_to_unix(value: int | float | None) -> int | None:
    """Convert an iMessage `date` to a Unix timestamp (seconds).

    Modern databases store nanoseconds since the Apple epoch; older ones store
    seconds. Distinguish by magnitude.
    """
    if not value:
        return None
    v = float(value)
    if v > 1e11:  # nanoseconds
        v = v / 1e9
    return int(v + APPLE_EPOCH)


def unix_to_local_iso(ts: int | None) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def norm_phone(value: str) -> str:
    """Normalize a handle for contact matching: emails lowercased, phone numbers
    reduced to their last 10 digits (US-friendly)."""
    v = (value or "").strip().lower()
    if "@" in v:
        return v
    digits = re.sub(r"\D", "", v)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def decode_attributed_body(blob: bytes | None) -> str | None:
    """Extract the plain text from a message `attributedBody` streamtyped blob.

    Since ~iOS 16 the `text` column is often NULL and the body lives here as a
    serialized NSAttributedString. This pulls the backing NSString out. It is a
    pragmatic parser (plain text, not attribute runs); good enough for search.
    """
    if not blob:
        return None
    try:
        marker = b"NSString"
        idx = blob.find(marker)
        if idx == -1:
            return None
        # After 'NSString' comes a small class/type preamble, then a length byte
        # (or a 0x81 marker introducing a 2-byte little-endian length).
        p = idx + len(marker) + 5
        if p >= len(blob):
            return None
        if blob[p] == 0x81:
            length = int.from_bytes(blob[p + 1 : p + 3], "little")
            start = p + 3
        else:
            length = blob[p]
            start = p + 1
        if length <= 0 or start + length > len(blob):
            return None
        return blob[start : start + length].decode("utf-8", errors="replace") or None
    except Exception:
        return None


def check_fts5() -> bool:
    """True if this Python's sqlite3 was compiled with FTS5."""
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        con.close()
        return True
    except sqlite3.OperationalError:
        return False
