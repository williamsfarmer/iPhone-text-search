# Quick Start (for non-programmers)

You will **not** write or edit any code. After a one-time setup, you use **two
icons on your Desktop** — no folders, no black terminal windows. Do the steps in
order.

---

## Part 1 — One-time setup (about 15 minutes)

**1. Install the Apple iPhone driver.**
Open the **Microsoft Store**, search for **Apple Devices**, and **Install** it.
(This is what lets your PC see your iPhone. Without it, the pull step later will
say "No iPhone detected." If you already have iTunes, you can skip this.)

**2. Install Python.**
Go to <https://www.python.org/downloads/>, click the big yellow **Download Python**
button, and run the file. On the very first screen, **check the box "Add python.exe
to PATH"**, then click **Install Now**. (That checkbox matters — don't skip it.)

**3. Download this tool.**
On the project's GitHub page, click the green **`< > Code`** button → **Download
ZIP**. Then, in your Downloads, **right-click the ZIP → Extract All**. You'll get a
folder called `iPhone-text-search`.

**4. Run Setup — once.**
Open that extracted folder and **double-click `Setup - Double Click Me`**.
   - If Windows shows a blue **"Windows protected your PC"** box (or asks "Do you
     want to run this file?"), that's normal for a downloaded tool — click
     **More info → Run anyway** (or **Run**).
   - Setup checks Python, installs the iPhone connector, and puts **two icons on
     your Desktop**. When it says *Done*, you're set.

**5. Turn off backup encryption (one time).**
In the **Apple Devices** app, click your iPhone and make sure **"Encrypt local
backup" is UNCHECKED**. (Your texts are still captured — encryption off just lets
the tool read them.)

That's the whole setup. From now on you only use the Desktop icons.

---

## Part 2 — Get your texts onto the PC

1. Plug your iPhone into the PC with a cable. **Unlock it.** If it asks **"Trust
   This Computer?"**, tap **Trust** and enter your passcode.
2. Double-click the **"Pull iPhone Texts"** icon on your Desktop.
3. Leave the phone unlocked and wait. When it finishes it prints a summary,
   including the **date range** of the texts it found — glance at that. If it
   doesn't go back as far as your texts really do, see **"Messages in iCloud"**
   below.

Repeat this any time you want to refresh with newer texts.

---

## Part 3 — Search your texts

Double-click the **"Search iPhone Texts"** icon, type what you're looking for
(plain words, no quotation marks needed), and press **Enter**. Only the messages
that match are shown. Press Enter on a blank line to quit.

**Or let Claude do it:** open Claude Code on this PC, in the tool folder, and ask
in plain English — *"search my texts for what the pharmacy said about the prior
auth."* It runs the search for you and reads back only the matches.

---

## Messages in iCloud (read this if your history looks short)

With **Messages in iCloud** on, your phone keeps recent texts and offloads older
ones to iCloud. The pull captures what's **on the phone**, so very old history may
be missing. Every pull prints the **date range** it captured. If that's shorter
than your real history: **Settings → [your name] → iCloud → See All → Messages**,
turn **Messages in iCloud** off and let it **"Download Messages to iPhone"** (pulls
everything down locally), then run **Pull iPhone Texts** again. You can turn it back
on afterward.

## Good to know

- **Where your texts are stored:** the searchable copy is saved in a **private
  per-user folder on this PC** (not in the tool folder, and not in OneDrive), so it
  isn't uploaded anywhere. Keep the tool folder where it is, though — the two
  Desktop icons point back to it.
- **Work/clinic PC:** managed computers sometimes block scripts. If Setup can't
  finish, use a personal PC.
- **Something went wrong?** In whatever window is open, right-click → **Select All**
  → **Enter** to copy everything, and paste it to Claude. The message is exactly
  what's needed to fix it — you don't have to interpret it.

## Words you'll see, in plain English

- **Desktop icons** — the two shortcuts Setup created; this is your whole UI.
- **Corpus** — the small private file holding your searchable texts.
- **Backup** — the temporary copy pulled from the phone; it's deleted automatically
  after your texts are extracted.
