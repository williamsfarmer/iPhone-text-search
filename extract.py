"""
extract.py -- pull iMessage/SMS out of a local iPhone backup into a clean,
searchable local corpus (corpus.db).

Nothing leaves your machine. This reads the backup that the Apple Devices app
(or iTunes) already made on this PC, copies the messages database out of it,
resolves contact names, decodes modern message bodies, and builds a small
SQLite database with a full-text index.

Usage (from a terminal in this folder):

    python extract.py                 # auto-pick the newest backup
    python extract.py --list          # just list the backups it can see
    python extract.py --backup 2      # pick backup #2 from --list
    python extract.py --backup "C:\\path\\to\\backup"
    python extract.py --out mydata.db # choose the output file (default corpus.db)

Encrypted backups are detected and explained (see README.md).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import common

HOME = "HomeDomain"
SMS_PATH = "Library/SMS/sms.db"
ADDRESSBOOK_PATH = "Library/AddressBook/AddressBook.sqlitedb"


def pick_backup(args) -> common.Backup | None:
    backups = common.find_backups()
    if not backups:
        print("No iPhone backups found in the usual Windows locations:")
        for r in common.BACKUP_ROOTS:
            print(f"    {r}")
        print("\nMake a backup first: open the Apple Devices app (or iTunes),")
        print("connect your iPhone, and choose 'Back up all of the data ... to")
        print("this computer'. See README.md for the click-by-click steps.")
        return None

    if args.list:
        print("Backups found (newest first):\n")
        for n, b in enumerate(backups, 1):
            print(f"  [{n}] {b.label()}\n")
        return None

    if args.backup:
        # Either an index into the list, or an explicit path.
        if args.backup.isdigit():
            i = int(args.backup) - 1
            if not (0 <= i < len(backups)):
                print(f"No backup #{args.backup}. Run with --list to see them.")
                return None
            return backups[i]
        p = Path(args.backup)
        return common.Backup(p, p.name, "?", _is_encrypted(p))

    return backups[0]


def _is_encrypted(path: Path) -> bool:
    for b in common.find_backups():
        if b.path == path:
            return b.encrypted
    return False


def load_contacts(ab_db: Path | None) -> dict[str, str]:
    """Map normalized phone/email -> display name from the backup's AddressBook."""
    contacts: dict[str, str] = {}
    if not ab_db or not ab_db.is_file():
        return contacts
    try:
        con = sqlite3.connect(f"file:{ab_db}?mode=ro", uri=True)
        rows = con.execute(
            """
            SELECT v.value, p.First, p.Last, p.Organization
            FROM ABMultiValue v
            JOIN ABPerson p ON v.record_id = p.ROWID
            WHERE v.value IS NOT NULL
            """
        ).fetchall()
        con.close()
    except Exception:
        return contacts
    for value, first, last, org in rows:
        name = " ".join(x for x in (first, last) if x).strip() or (org or "")
        if not name:
            continue
        contacts[common.norm_phone(str(value))] = name
    return contacts


def build_corpus(sms_db: Path, contacts: dict[str, str], out: Path) -> dict:
    src = sqlite3.connect(f"file:{sms_db}?mode=ro", uri=True)
    src.text_factory = bytes  # we decode text ourselves (attributedBody is binary)

    if out.exists():
        out.unlink()
    dst = sqlite3.connect(out)
    dst.executescript(
        """
        CREATE TABLE messages(
            id        INTEGER PRIMARY KEY,
            guid      TEXT,
            ts        INTEGER,   -- unix seconds
            datetime  TEXT,      -- local YYYY-MM-DD HH:MM
            direction TEXT,      -- 'sent' or 'received'
            contact   TEXT,      -- resolved name, or raw handle
            handle    TEXT,      -- raw phone/email
            chat      TEXT,      -- group/chat display name if any
            text      TEXT
        );
        CREATE VIRTUAL TABLE messages_fts USING fts5(
            text, contact, content='messages', content_rowid='id'
        );
        """
    )

    def dec(v):
        return v.decode("utf-8", errors="replace") if isinstance(v, (bytes, bytearray)) else v

    query = """
        SELECT
            m.ROWID, m.guid, m.date, m.is_from_me, m.text, m.attributedBody,
            h.id AS handle,
            (SELECT c.display_name FROM chat c
             JOIN chat_message_join cmj ON cmj.chat_id = c.ROWID
             WHERE cmj.message_id = m.ROWID LIMIT 1) AS chat_name
        FROM message m
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        ORDER BY m.date ASC
    """

    total = 0
    with_text = 0
    min_ts = None
    max_ts = None
    rows = []
    for r in src.execute(query):
        rowid, guid, date, is_from_me, text, abody, handle, chat_name = r
        total += 1

        body = dec(text)
        if not body:
            body = common.decode_attributed_body(abody)
        body = (body or "").strip()

        ts = common.apple_time_to_unix(date)
        if ts:
            min_ts = ts if min_ts is None else min(min_ts, ts)
            max_ts = ts if max_ts is None else max(max_ts, ts)

        handle_s = dec(handle) or ""
        chat_s = dec(chat_name) or ""
        contact = contacts.get(common.norm_phone(handle_s), handle_s) if handle_s else "me"
        direction = "sent" if is_from_me else "received"

        if body:
            with_text += 1
        rows.append(
            (
                rowid, dec(guid), ts, common.unix_to_local_iso(ts),
                direction, contact, handle_s, chat_s, body,
            )
        )

    dst.executemany(
        "INSERT INTO messages(id,guid,ts,datetime,direction,contact,handle,chat,text) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        rows,
    )
    # Only index rows that actually have text.
    dst.execute(
        "INSERT INTO messages_fts(rowid, text, contact) "
        "SELECT id, text, contact FROM messages WHERE text <> ''"
    )
    dst.commit()

    n_contacts = dst.execute(
        "SELECT COUNT(DISTINCT contact) FROM messages WHERE contact <> 'me'"
    ).fetchone()[0]
    dst.close()
    src.close()

    return {
        "total": total,
        "with_text": with_text,
        "contacts": n_contacts,
        "start": common.unix_to_local_iso(min_ts),
        "end": common.unix_to_local_iso(max_ts),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract iPhone texts into a local searchable corpus.")
    ap.add_argument("--list", action="store_true", help="list backups and exit")
    ap.add_argument("--backup", help="backup index (from --list) or an explicit path")
    ap.add_argument("--out", default="corpus.db", help="output database (default: corpus.db)")
    args = ap.parse_args()

    if not common.check_fts5():
        print("This Python's sqlite3 was built without FTS5 full-text search.")
        print("Install Python from python.org (its Windows build includes FTS5).")
        return 2

    backup = pick_backup(args)
    if backup is None:
        return 0 if args.list else 1

    print(f"Using backup: {backup.device}  ({backup.last_backup})")
    print(f"  {backup.path}")

    if backup.encrypted:
        print(
            "\nThis backup is ENCRYPTED, so the messages database can't be read "
            "directly.\nEasiest fix (one time):\n"
            "  1. Apple Devices app > your iPhone > General/Backups.\n"
            "  2. Uncheck 'Encrypt local backup' (you'll need the backup password),\n"
            "     or on the phone reset it: Settings > General > Transfer or Reset\n"
            "     iPhone > Reset > Reset All Settings (resets the backup password only).\n"
            "  3. Make a fresh backup, then re-run this tool.\n"
            "See README.md for the encrypted-backup notes."
        )
        return 1

    sms_db = common.locate_in_backup(backup.path, HOME, SMS_PATH)
    if not sms_db:
        print("\nCouldn't find the messages database inside this backup.")
        print("Make sure the backup completed and includes device data.")
        return 1

    ab_db = common.locate_in_backup(backup.path, HOME, ADDRESSBOOK_PATH)
    contacts = load_contacts(ab_db)
    print(f"Contacts resolved from backup: {len(contacts)}")

    out = Path(args.out).resolve()
    print("Building corpus (decoding message bodies, this can take a moment)...")
    stats = build_corpus(sms_db, contacts, out)

    print("\nDone.")
    print(f"  Corpus:   {out}")
    print(f"  Messages: {stats['total']:,}  ({stats['with_text']:,} with searchable text)")
    print(f"  Contacts: {stats['contacts']:,}")
    if stats["start"]:
        print(f"  Range:    {stats['start']}  ->  {stats['end']}")
    print("\nNow search it:  python search.py \"your keywords\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
