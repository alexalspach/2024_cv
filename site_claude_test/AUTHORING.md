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

3. **Add ONE record to `cv/data/projects.json`**, under `"projects"` (copy an existing one).
   Everything about the project lives in this single block. Put it where you want it to appear —
   the page order follows this file, newest at the top.

   ```jsonc
   "MyRobot": {
     "year": "2025",
     "featured": false,
     "tags": ["soft", "h/w dev"],                 // friendly names OR codes — both work
     "tocTitle": "My Robot: the longer title for the contents list",

     "thumb": "MyRobotthumb.jpg",                 // the square grid picture...
     "gridTitle": "My Robot",                     // ...its bold label...
     "role": "What I did",                        // ...and the small line under it
     "hero_img": "assets/images/projects/MyRobot/photo.jpg",  // optional: auto-make the
     "crop": "top"                                // square thumb from this photo (crop optional)
   }
   ```

   - Have a pre-made square thumbnail? Just give `thumb` (skip `hero_img`/`crop`).
   - Want the computer to make the thumbnail? Give `hero_img` (a full-size photo) and it crops a
     square for you; add `crop` to choose which part (see below).
   - **No grid picture at all?** Leave out `thumb`, `gridTitle`, `role` — it still gets a
     contents entry and a full write-up, just no tile in the top grid.

4. **Run** `python3 tools/build.py`.

**What the computer does for you:** makes the square thumbnail, then adds the project to the
picture grid, the contents list, and as a full write-up — all with the **same tags** — and files
it under the right **year** automatically. Everything comes from that one record, so the three
places can never drift apart, and there's no separate list or order to keep in sync.

> **Tags** are the little filter buttons (soft, tactile, humanoids, tri…). List the ones that fit
> in `tags` — you type them once and they apply everywhere. You can write the **friendly** name
> off the button (`design/mfg`, `h/w dev`, `vision`, `toyota (tri)`) or the short code
> (`designmfg`, `hwdev`, `computervision`, `tri`); the build understands both.

> **Notes in the file:** `cv/data/projects.json` allows `//` comments (and a stray trailing comma
> won't break the build), so you can leave yourself reminders. There's a tag cheat-sheet comment
> near the top.

### Choosing which part of the photo becomes the thumbnail

The grid thumbnails are **squares**, but your photo usually isn't. By default the computer keeps
the **middle** of the photo. If the good part is off to one side (a face in the top corner, a
robot on the left…), add a **`"crop"`** to the project's record (only matters when you use a
`hero_img`) to say which part to keep:

- **A spot by name:** `center` (default), `top`, `bottom`, `left`, `right`,
  `top-left`, `top-right`, `bottom-left`, `bottom-right`.
- **An exact spot:** `"30% 10%"` — first number is left→right (0% = far left, 100% = far right),
  second is top→bottom (0% = top, 100% = bottom). So `"50% 0%"` is the same as `top`.

```jsonc
"MyRobot": {
  "year": "2025", "tags": ["soft"], "tocTitle": "…",
  "thumb": "MyRobotthumb.jpg", "gridTitle": "My Robot", "role": "What I did",
  "hero_img": "assets/images/projects/MyRobot/photo.jpg",
  "crop": "top"
}
```

Because your photo didn't change, a normal build won't redo the thumbnail — so after changing a
crop, rebuild with **`python3 tools/build.py --force-thumbs`** to see the new crop. (Prefer to
just eyeball it first? `python3 tools/gen_thumb.py photo.jpg try.jpg 400 top` writes one test
thumbnail you can open.)

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
| Rebuild + redo every thumbnail (after a `crop` change) | `python3 tools/build.py --force-thumbs` |
| Look at the site | `./startServer.sh` → http://localhost:8000/cv/ |
| Make sure nothing broke | `tests/.venv/bin/python tests/test_cv.py` |
| Try one thumbnail crop by hand | `python3 tools/gen_thumb.py photo.jpg out.jpg 400 top` |

That's the whole system: **edit a small file, run one command, refresh the page.**

*(Work experience — `cv/experience.html` — is still edited by hand for now. Everything else is built from the fact files above.)*
