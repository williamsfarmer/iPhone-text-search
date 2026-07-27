"""
search.py -- search the local corpus built by extract.py.

The corpus (corpus.db) lives on this machine. This command reads it locally and
prints only the messages that match -- so if you point Claude at this tool, the
only text that ever leaves the machine is the handful of lines a query returns,
not your whole message history.

Examples:

    python search.py "biopsy results"
    python search.py "dinner" --contact "Jane"
    python search.py "" --contact "Mom" --after 2026-01-01
    python search.py "referral" --from-me --limit 20
    python search.py "post-op" --json          # machine-readable, for Claude

Query terms are ANDed by default. Use --raw to pass a literal FTS5 expression
(e.g. 'biopsy OR pathology', '"exact phrase"', 'derm*').
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def to_ts(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())


def build_match(query: str, raw: bool) -> str:
    """Turn a plain query into a safe FTS5 MATCH expression (terms ANDed)."""
    if raw:
        return query
    terms = re.findall(r"[^\s]+", query)
    # Quote each term so punctuation can't break FTS5 syntax; space = AND.
    return " ".join('"' + t.replace('"', '""') + '"' for t in terms)


def main() -> int:
    ap = argparse.ArgumentParser(description="Search your local iPhone-text corpus.")
    ap.add_argument("query", nargs="?", default="", help="keywords to search for")
    ap.add_argument("--db", default="corpus.db", help="corpus database (default: corpus.db)")
    ap.add_argument("--contact", help="only messages to/from this contact (substring match)")
    ap.add_argument("--from-me", action="store_true", help="only messages you sent")
    ap.add_argument("--to-me", action="store_true", help="only messages you received")
    ap.add_argument("--after", help="on/after this date (YYYY-MM-DD)")
    ap.add_argument("--before", help="before this date (YYYY-MM-DD)")
    ap.add_argument("--limit", type=int, default=50, help="max results (default: 50)")
    ap.add_argument("--raw", action="store_true", help="treat query as a literal FTS5 expression")
    ap.add_argument("--json", action="store_true", help="output JSON")
    args = ap.parse_args()

    db = Path(args.db)
    if not db.is_file():
        print(f"No corpus found at {db.resolve()}.\nRun:  python extract.py")
        return 1

    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    where = []
    params: list = []

    if args.query.strip():
        base = (
            "SELECT m.datetime, m.direction, m.contact, m.handle, m.chat, m.text "
            "FROM messages_fts f JOIN messages m ON m.id = f.rowid "
            "WHERE messages_fts MATCH ?"
        )
        params.append(build_match(args.query, args.raw))
    else:
        # No text query: browse by the metadata filters only.
        base = (
            "SELECT m.datetime, m.direction, m.contact, m.handle, m.chat, m.text "
            "FROM messages m WHERE m.text <> ''"
        )

    if args.contact:
        where.append("(m.contact LIKE ? OR m.handle LIKE ?)")
        params += [f"%{args.contact}%", f"%{args.contact}%"]
    if args.from_me:
        where.append("m.direction = 'sent'")
    if args.to_me:
        where.append("m.direction = 'received'")
    if args.after:
        where.append("m.ts >= ?")
        params.append(to_ts(args.after))
    if args.before:
        where.append("m.ts < ?")
        params.append(to_ts(args.before))

    sql = base
    if where:
        sql += " AND " + " AND ".join(where)
    sql += " ORDER BY m.ts DESC LIMIT ?"
    params.append(args.limit)

    try:
        rows = con.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        print(f"Search error: {e}\n(Try --raw off, or simpler keywords.)")
        return 1
    finally:
        con.close()

    if args.json:
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
        return 0

    if not rows:
        print("No matches.")
        return 0

    print(f"{len(rows)} match(es):\n")
    for r in rows:
        arrow = "->" if r["direction"] == "sent" else "<-"
        who = r["contact"] or r["handle"] or "?"
        chat = f" [{r['chat']}]" if r["chat"] else ""
        text = " ".join((r["text"] or "").split())
        print(f"{r['datetime']}  {arrow} {who}{chat}")
        print(f"    {text}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
