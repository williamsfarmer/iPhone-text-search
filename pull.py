"""
pull.py -- Option B: pull ONLY the messages off the iPhone, no full-phone dump.

This drives `pymobiledevice3` (a pure-Python implementation of Apple's device
protocols) to make a local backup into a *scratch* folder you choose -- put it on
an external drive if you like -- then lifts out just the messages database and
your contacts, builds the searchable corpus, and deletes the scratch backup.

Net result: the only thing left on disk is the small corpus.db. No 97 GB of
photos/attachments ever stays on your machine.

Prerequisites (one time):
    * The Apple Devices app (or iTunes) installed -- provides the Windows driver
      that lets a computer talk to the iPhone.
    * pip install pymobiledevice3
    * iPhone plugged in, unlocked, and "Trust This Computer" tapped.
    * Backup encryption OFF (Apple Devices app > your phone > uncheck
      "Encrypt local backup"). Texts are included in unencrypted backups.

Usage:
    python pull.py                          # scratch in ./_backup_scratch, auto-deleted
    python pull.py --scratch E:\scratch     # stage the backup on an external drive
    python pull.py --keep                   # keep the raw backup (debugging)
    python pull.py --out corpus.db          # choose the output database

Because Messages in iCloud may keep older history only in the cloud, check the
date range this prints against how far back your texts really go. If it looks
truncated, see README.md ("Messages in iCloud").
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import common
import extract  # reuse the tested load_contacts + build_corpus

HOME = extract.HOME
SMS_PATH = extract.SMS_PATH
ADDRESSBOOK_PATH = extract.ADDRESSBOOK_PATH


def pmd3_cmd() -> list[str] | None:
    """Return how to invoke pymobiledevice3 on this machine, or None if missing."""
    if shutil.which("pymobiledevice3"):
        return ["pymobiledevice3"]
    # Fall back to the module form in case the console script isn't on PATH.
    try:
        subprocess.run(
            [sys.executable, "-m", "pymobiledevice3", "version"],
            capture_output=True, check=True,
        )
        return [sys.executable, "-m", "pymobiledevice3"]
    except Exception:
        return None


def device_present(base: list[str]) -> bool:
    """Best-effort check that an iPhone is connected and reachable."""
    try:
        r = subprocess.run(
            base + ["usbmux", "list"], capture_output=True, text=True, timeout=30
        )
    except Exception:
        return False
    out = (r.stdout or "") + (r.stderr or "")
    # A connected device prints a JSON array with at least one entry.
    return r.returncode == 0 and ("Identifier" in out or "UniqueDeviceID" in out or "SerialNumber" in out)


def run_backup(base: list[str], scratch: Path) -> bool:
    scratch.mkdir(parents=True, exist_ok=True)
    cmd = base + ["backup2", "backup", "--full", str(scratch)]
    print("Backing up messages (this talks to the phone; leave it unlocked)...")
    print("  " + " ".join(cmd))
    try:
        # Inherit stdout/stderr so backup progress is visible live.
        r = subprocess.run(cmd)
    except FileNotFoundError:
        print("Could not launch pymobiledevice3. Is it installed? (pip install pymobiledevice3)")
        return False
    if r.returncode != 0:
        print(
            "\nBackup command failed. Common causes:\n"
            "  * iPhone locked or 'Trust This Computer' not tapped.\n"
            "  * Apple Devices app / Apple Mobile Device Service not installed.\n"
            "  * Backup encryption is ON -- turn it off and retry.\n"
            "  * Not enough free disk space (needs roughly as much free space as\n"
            "    your phone's on-device data; use --scratch on a bigger drive).\n"
            "You can also run the command above by hand to see the full error."
        )
        return False
    return True


def find_backup_dir(scratch: Path) -> Path | None:
    """pymobiledevice3 writes into <scratch>/<UDID>/. Find that folder."""
    for child in scratch.iterdir():
        if child.is_dir() and (child / "Manifest.plist").is_file():
            return child
    # Some versions back up directly into the target dir.
    if (scratch / "Manifest.plist").is_file():
        return scratch
    return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pull only your iPhone messages into a local searchable corpus."
    )
    ap.add_argument("--scratch", default=None,
                    help="temporary backup folder (put on an external drive if short on space)")
    ap.add_argument("--out", default=None,
                    help="output database (default: a private per-user folder)")
    ap.add_argument("--keep", action="store_true", help="keep the raw scratch backup")
    args = ap.parse_args()

    if not common.check_fts5():
        print("This Python's sqlite3 was built without FTS5. Install Python from python.org.")
        return 2

    base = pmd3_cmd()
    if not base:
        print(
            "pymobiledevice3 isn't installed.\n"
            "  pip install pymobiledevice3\n"
            "Then plug in your iPhone, unlock it, and tap 'Trust This Computer'."
        )
        return 2

    if not device_present(base):
        print(
            "No iPhone detected.\n"
            "  1. Plug the phone in with a data cable.\n"
            "  2. Unlock it and tap 'Trust This Computer' (enter your passcode).\n"
            "  3. Make sure the Apple Devices app (or iTunes) is installed.\n"
            "Then re-run:  python pull.py"
        )
        return 1

    scratch = Path(args.scratch).resolve() if args.scratch \
        else (common.default_data_dir() / "_scratch")
    if not run_backup(base, scratch):
        return 1

    backup_dir = find_backup_dir(scratch)
    if not backup_dir:
        print("Backup finished but no backup folder was found under the scratch path.")
        return 1

    if common.locate_in_backup(backup_dir, HOME, SMS_PATH) is None:
        # Could be encryption or an incomplete backup.
        enc = False
        try:
            import plistlib
            with open(backup_dir / "Manifest.plist", "rb") as fh:
                enc = bool(plistlib.load(fh).get("IsEncrypted", False))
        except Exception:
            pass
        if enc:
            print("\nThis backup is ENCRYPTED, so the messages can't be read. Turn off\n"
                  "'Encrypt local backup' in the Apple Devices app and run pull.py again.")
        else:
            print("\nCouldn't find the messages database in the backup (it may be incomplete).")
        return 1

    sms_db = common.locate_in_backup(backup_dir, HOME, SMS_PATH)
    ab_db = common.locate_in_backup(backup_dir, HOME, ADDRESSBOOK_PATH)
    contacts = extract.load_contacts(ab_db)
    print(f"Contacts resolved from backup: {len(contacts)}")

    out = Path(args.out).resolve() if args.out else common.default_corpus_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    print("Building corpus (decoding message bodies)...")
    stats = extract.build_corpus(sms_db, contacts, out)

    if not args.keep:
        print("Deleting the scratch backup (keeping only the corpus)...")
        shutil.rmtree(scratch, ignore_errors=True)

    print("\nDone.")
    print(f"  Corpus:   {out}")
    print(f"  Messages: {stats['total']:,}  ({stats['with_text']:,} with searchable text)")
    print(f"  Contacts: {stats['contacts']:,}")
    if stats["start"]:
        print(f"  Range:    {stats['start']}  ->  {stats['end']}")
        print("  ^ Check this covers how far back your texts go. If it looks short,")
        print("    see README.md 'Messages in iCloud'.")
    print("\nNow double-click the 'Search iPhone Texts' icon on your Desktop to look through them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
