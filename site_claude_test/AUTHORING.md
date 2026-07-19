# How to edit the site (start here)

You almost never touch the big web pages by hand anymore. Instead you fill in a few small
**fact files**, then run **one command** that builds the pages for you.

Think of it like a mail‑merge: you type the facts once, and the computer stamps them into all
the places they need to go (the picture grid, the contents list, the full write‑up, the
homepage…). No more copy‑pasting the same thing in three spots.

---

## The only command you really need

After you change anything, run this from the site folder:

```bash
python3 tools/build.py
```

That rebuilds the pages. To look at the site in a browser:

```bash
./startServer.sh          # then open http://localhost:8000/cv/
```

If the page looks out of date, press **Cmd+Shift+R** to force a fresh load.

---

## Where things live

**You edit these** (small, simple files):

| Thing | File |
|---|---|
| Facts about a project | `cv/data/projects.json` |
| A project's write‑up (its card) | `cv/projects/<name>.html` |
| A project's short homepage version | `cv/projects/<name>.teaser.html` |
| Facts about papers & patents | `cv/data/publications.json` |
| A paper's write‑up (its card) | `cv/pubs/<name>.html` |

**The computer writes these — don't edit them by hand** (your changes would be overwritten):
`cv/projects.html`, `cv/paperspatents.html`, and the "Featured projects" box on the homepage.

`<name>` is just a short nickname/id for the item, e.g. `Punyo2`. It has no spaces.

---

## Add a new project

1. **Drop in a photo** anywhere under `assets/`, e.g.
   `assets/images/projects/MyRobot/photo.jpg` (any size or shape is fine).

2. **Write the project's story** in a new file `cv/projects/MyRobot.html`.
   Easiest way: open an existing one and copy it, then change the words.

3. **Add it to `cv/data/projects.json`** in three spots (copy an existing entry as a template):

   ```jsonc
   // (a) the facts — under "projects"
   "MyRobot": { "year": "2025", "featured": false,
                "tags": ["soft","hwdev"],
                "tocTitle": "My Robot: the longer title for the contents list" },

   // (b) its thumbnail tile — in the "grid" list
   { "target": "MyRobot", "thumb": "MyRobotthumb.jpg",
     "title": "My Robot", "role": "What I did",
     "hero_img": "assets/images/projects/MyRobot/photo.jpg" },

   // (c) its place in the list — add the name to "cardOrder"
   "MyRobot"
   ```

4. **Run** `python3 tools/build.py`.

**What the computer does for you:** crops your photo into a tidy square thumbnail, adds the
project to the picture grid, the contents list, and as a full card — all with the **same tags**
— and files it under the right **year** automatically. (The contents list follows the card
order and groups by year, so there's nothing else to line up.)

> **Tags** are the little filter buttons (soft, tactile, humanoids, tri…). Just list the ones
> that fit in `tags` — you only type them once and they apply everywhere.

---

## Add a paper

1. **Write the paper's card** in `cv/pubs/MyPaper.html` (copy an existing one).
2. **Add one line** to `"entries"` in `cv/data/publications.json`:

   ```jsonc
   { "type": "journal", "year": "2025", "id": "MyPaper",
     "tocTitle": "The Title (Where It Appeared)", "award": false }
   ```

   - `type` is one of: `journal`, `conference`, `thesis`, `bookchapter`, `blog`.
   - `award: true` adds a 🏆 next to it.
   - A **blog post** has no card — use `"card": false` and `"url": "https://…"` instead of `id`.
3. **Run** `python3 tools/build.py`.

## Add a patent

Patents are just a list — no write‑up. Add one line to `"patents"` in `publications.json`:

```jsonc
{ "year": "2025", "number": "12311529", "title": "What the patent is" }
```

Run the build. The link and the "(US…)" number are filled in from `number` for you.

---

## Put a project on the homepage

1. Write a **short** version in `cv/projects/MyRobot.teaser.html` (copy an existing teaser).
2. Add `"MyRobot"` to the `indexFeatured` list in `cv/data/projects.json`.
3. Build.

(The homepage and the CV page have different styling, so the same card looks right on both.)

## Hide something without deleting it

Add `"hidden": true` to a project's facts in `projects.json`. It vanishes from the site but
stays in the file, and its write‑up is kept safe. Delete that line to bring it back.
(JSON files can't have real "comment out" marks, so this on/off switch does the same job.)

---

## Cheat sheet

| I want to… | Do this |
|---|---|
| Rebuild the pages | `python3 tools/build.py` |
| Look at the site | `./startServer.sh` → http://localhost:8000/cv/ |
| Make sure nothing broke | `tests/.venv/bin/python tests/test_cv.py` |
| Make one square thumbnail by hand | `python3 tools/gen_thumb.py photo.jpg output.jpg` |

That's the whole system: **edit a small file, run one command, refresh the page.**

*(Work experience — `cv/experience.html` — is still edited by hand for now. Everything else is built from the fact files above.)*
