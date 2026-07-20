#!/usr/bin/env python3
# =============================================================================
#  dataio.py  —  a forgiving loader for the data files (projects.json etc.).
#
#  Plain JSON is strict: no notes/comments, and one stray comma breaks it. Since
#  you hand-edit these files, this loader is lenient so small slips don't stop a
#  build. On top of normal JSON it also allows:
#     - notes:   // like this   and   /* like this */
#     - a leftover comma before a closing ]  or  }   (a "trailing comma")
#  Everything else is normal JSON. Both build scripts read their data through here.
# =============================================================================
import json


def _strip_comments(text):
    """Remove // line and /* block */ comments, but NOT ones inside quoted strings
    (so a URL like http://… or a title with /slashes/ is left untouched)."""
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:                                  # inside "a string": copy verbatim
            out.append(c)
            if c == "\\" and i + 1 < n:             # keep escaped char (e.g. \")
                out.append(text[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':                                # a string starts
            in_str = True; out.append(c); i += 1; continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":       # // line comment
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":       # /* block comment */
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2; continue
        out.append(c); i += 1
    return "".join(out)


def _strip_trailing_commas(text):
    """Drop a comma that is immediately followed (ignoring spaces) by } or ] — again
    leaving anything inside quoted strings alone."""
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if c == ",":
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if j < n and text[j] in "}]":           # a trailing comma -> skip it
                i += 1; continue
        out.append(c); i += 1
    return "".join(out)


def load(path):
    """Read a .json file, tolerating comments and trailing commas, and return the data.
    Raises the normal json error (with a helpful location) if something else is wrong."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return json.loads(_strip_trailing_commas(_strip_comments(text)))
