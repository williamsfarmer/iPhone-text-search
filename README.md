# iPhone Text Search (Windows)

Search your own iPhone texts (iMessage **and** green-bubble SMS) from your PC, so
Claude can find things in them — **without your whole message history, or 97 GB of
photos, going to the cloud or sitting on your disk.**

> **Not a programmer? Start with [QUICKSTART.md](QUICKSTART.md)** — a click-by-click
> guide with no jargon. This README is the fuller reference for when you want detail.

## How it stays private

1. Your messages get pulled into a small local search database (`corpus.db`). This
   file **never leaves your machine.**
2. When you (or Claude) search, only the **messages that match** a query are shown —
   so you can search tens of thousands of texts and the cloud only ever sees the
   handful that hit. Same local-first idea as a de-id proxy.

`corpus.db` and anything derived from a backup are git-ignored, so nothing sensitive
gets committed.

## The important fact about size

Your searchable **text** is a single small database (usually a few hundred MB). The
huge "Messages" number on your phone is almost entirely **attachments** (photos,
videos, voice memos) — which you don't need to search text. This tool keeps only the
text database, so the thing left on your disk is tiny.

---

## The easy way: Setup + two Desktop icons

Most people should just follow **[QUICKSTART.md](QUICKSTART.md)**: install the Apple
Devices app + Python, download and extract this tool, then **double-click
`Setup - Double Click Me`** once. It installs the connector and creates two Desktop
icons — **Pull iPhone Texts** and **Search iPhone Texts** — and you never touch a
folder or terminal again. The rest of this README is the technical reference behind
those icons.

## Two ways to get the messages

### Option B — pull *only* the messages off the phone (recommended)

`pull.py` (run by the **Pull iPhone Texts** icon) talks to the iPhone directly, makes
a backup into a scratch folder, lifts out just the messages database + your contacts,
builds the corpus, and **deletes the scratch backup**. Nothing large is left behind.

Prerequisites: the **Apple Devices** app (the Windows iPhone driver), Python with
`pymobiledevice3` installed (Setup does this), and **backup encryption OFF** in the
Apple Devices app. Then plug in the iPhone, unlock it, and tap **Trust This Computer**.

Advanced (from a terminal, instead of the icon):
```
python pull.py                       # default private scratch, auto-deleted after
python pull.py --scratch E:\scratch  # stage the temporary backup on another drive
```

### Option A — use a backup you already made

If you'd rather make the backup yourself in the Apple Devices app (full phone backup),
point the extractor at it (terminal):
```
python extract.py            # auto-finds your latest backup
python extract.py --list     # show all backups it can see
```

Either way, you end up with the corpus (a private per-user `corpus.db`, see below).

---

## Searching

Double-click the **Search iPhone Texts** icon, type words, press Enter. Advanced
users can call it directly:
```
python search.py "biopsy results"
python search.py "dinner" --contact "Jane"
python search.py "referral" --from-me --after 2026-01-01
python search.py "" --contact "Mom" --before 2026-06-01
```

| Flag | Meaning |
|------|---------|
| `--contact NAME` | only messages to/from a contact (name or number, partial ok) |
| `--from-me` / `--to-me` | only messages you sent / received |
| `--after YYYY-MM-DD` / `--before YYYY-MM-DD` | date range |
| `--limit N` | max results (default 50) |
| `--raw` | literal search expression, e.g. `"biopsy OR pathology"`, `"derm*"` |
| `--json` | machine-readable output |

## Letting Claude search for you

Run Claude Code **on this PC, in this folder.** Ask something like *"search my texts
for what the pharmacy said about the prior auth."* It runs `search.py` locally and reads
back only the matching messages — the full corpus never leaves the machine.

## Messages in iCloud (read this if history looks short)

With **Messages in iCloud** turned on, your phone keeps recent messages locally and may
offload older ones (and most attachments) to iCloud. A local backup captures whatever is
**on the device**, so:

- The good part: offloaded attachments aren't on the phone, so the backup stays small.
- The watch-out: very old history might live only in iCloud and not be captured.

Every run prints the **date range** it captured. If that looks shorter than your real
history, download everything to the phone first: **Settings → [your name] → iCloud →
See All → Messages**, toggle **Messages in iCloud** off, and let it "Download Messages
to iPhone" (this pulls the full history down locally). Re-run `pull.py`, then you can
turn it back on.

## Notes & limits

- **Where the corpus lives:** by default in a private per-user folder
  (`%LOCALAPPDATA%\iPhoneTextSearch\corpus.db`), which is **not** synced to OneDrive.
  This is deliberate — the corpus holds your whole decoded text history and must not
  land in a cloud-synced folder. Override with `--out` / `--db` if you want.
- **Snapshot:** the corpus reflects the last pull. Run **Pull iPhone Texts** again to
  pick up newer texts.
- **Text only:** attachments (photos/files) aren't indexed — just message text.
- **Message bodies:** modern iOS stores text in a binary field; this decodes the plain
  text of each message (good for search). Rich attributes / some edits aren't reconstructed.
- **Contacts** come from the backup's address book; unknown numbers show as the number.
- **PHI:** your texts may contain patient-adjacent content. The corpus stays on this
  machine (private folder above) — don't upload it; the default workflow is built so you
  never have to.

## Files

| File | What it is |
|------|------------|
| `Setup - Double Click Me.bat` | one-time setup: checks Python, installs the connector, makes the Desktop icons |
| `launch-pull.bat` | target of the **Pull iPhone Texts** icon |
| `launch-search.bat` | target of the **Search iPhone Texts** icon |
| `make-shortcuts.ps1` | creates the two Desktop shortcuts (run by Setup) |
| `pull.py` | **Option B** — pull only the messages off the phone, build the corpus |
| `extract.py` | **Option A** — build the corpus from a backup you already made |
| `search.py` | search the corpus |
| `common.py` | shared helpers (backup location, message-body decoding, corpus path) |
| `extract.bat` | terminal wrapper for Option A |
| `requirements.txt` | `pymobiledevice3` (only needed for `pull.py`) |
| `QUICKSTART.md` | click-by-click guide for non-programmers |
