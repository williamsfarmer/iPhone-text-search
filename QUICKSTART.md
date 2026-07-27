# Quick Start (for non-programmers)

You will **not** edit any code. Everything below is either a button to click or a
line to **copy and paste** into a black terminal window. Do the steps in order.
The full details live in `README.md`; this is the short version.

---

## Part 1 — One-time setup (about 15 minutes, done once)

**1. Install the Apple driver.**
Open the **Microsoft Store**, search for **Apple Devices**, and Install it. (This is
what lets your PC talk to your iPhone. If you already have iTunes, you're set.)

**2. Install Python.**
Go to <https://www.python.org/downloads/> and click the big yellow **Download Python**
button. Run the file you downloaded. On the very first screen, **check the box that
says "Add python.exe to PATH"**, then click **Install Now**. (That checkbox matters —
don't skip it.)

**3. Get this tool onto your PC.**
On this project's GitHub page, click the green **`< > Code`** button, then **Download
ZIP**. Save it somewhere easy like your **Desktop**, then **right-click the ZIP →
Extract All**. You'll get a folder called `iPhone-text-search`.

**4. Open a terminal inside that folder.** *(This is the one non-obvious trick.)*
   - Open the `iPhone-text-search` folder in File Explorer so you see the files inside it.
   - Click once in the **address bar** at the top (where the folder path is shown).
   - Type `cmd` and press **Enter**.
   - A black window opens. This is the "terminal." It's already pointing at the folder.

**5. Install the one add-on.** In that black window, copy-paste this and press Enter:
```
pip install pymobiledevice3
```
Wait for it to finish (a lot of text scrolls by — that's normal).

You're done with setup.

---

## Part 2 — Pull your texts onto the PC

**1.** In the Apple Devices app, click your iPhone, and make sure **"Encrypt local
backup" is UNCHECKED**.

**2.** Plug your iPhone into the PC. Unlock it. If it asks **"Trust This Computer?"**,
tap **Trust** and enter your passcode.

**3.** In the black terminal window (from Part 1, step 4), copy-paste this and press Enter:
```
python pull.py
```
Leave the phone unlocked and wait. When it finishes it prints a summary, including the
**date range** of the texts it found. Glance at that — if it doesn't go back as far as
your real texts do, see the **"Messages in iCloud"** section in `README.md`.

That's it — your texts are now in a small local file called `corpus.db`. You can repeat
Part 2 any time to refresh it with newer texts.

---

## Part 3 — Search your texts

In the same black terminal window, put your search in **quotes** after `python search.py`:
```
python search.py "biopsy results"
python search.py "dinner plans" --contact "Jane"
python search.py "referral" --after 2026-01-01
```
Only the messages that match are shown.

**Prefer to let Claude do the searching?** Open Claude Code on this PC, inside the
`iPhone-text-search` folder, and just ask in plain English — *"search my texts for what
the pharmacy said about the prior auth."* It runs the search for you and reads back only
the matches. Nothing else leaves your machine.

---

## If something goes wrong

Copy the **entire** contents of the black window (right-click → Select All → Enter to
copy) and paste it to Claude. The error text is exactly what's needed to fix it — you
don't have to interpret it yourself.

## Words you'll see, in plain English

- **Terminal / Command Prompt** — the black window you paste commands into.
- **Corpus (`corpus.db`)** — the small local file holding your searchable texts.
- **Backup** — the temporary copy pulled off the phone; `pull.py` deletes it afterward.
