# Automatic checks

This is a robot that opens the site in a real browser and makes sure nothing is broken —
so you don't have to click around and hunt for problems yourself.

## Run it

```bash
tests/.venv/bin/python tests/test_cv.py
```

- Prints `PASS`/`FAIL` for each check and a total at the end.
- Green (exit 0) = all good. Red (exit 1) = it prints exactly what broke.
- Add `--headed` to watch it happen in a visible window.

## One‑time setup (only if the `tests/.venv` folder is missing)

```bash
python3 -m venv tests/.venv
tests/.venv/bin/pip install playwright
```

It uses the Google Chrome already on your Mac, so there's no big download.

## What it checks (in plain terms)

1. The pages load with **no errors** and **no missing images/files**.
2. Clicking a project **scrolls to it** and lands in the right spot.
3. The **filter buttons** (soft, tactile, …) show/hide the right things.
4. Links like `.../cv/#projects/Punyo2` jump straight to that project.
5. The videos load **a few at a time** while scrolling (this is what stops phones from crashing).
6. The **contents list** keeps its table layout.
7. The publications page works and its **PDF links aren't broken**.
8. The homepage's **featured cards** show up with working images and links.

If you ever change the build scripts, run this afterward — it's the safety net.
