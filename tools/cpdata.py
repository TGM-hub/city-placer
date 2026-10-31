"""City Placer data: DATA lives in index.html (const DATA={...}), the cities in data/cities-<continent>.js.

load_data(root)  -> DATA with DATA["cities"] filled back from data/cities-*.js (for the build tools)
"""
import json
import re
from pathlib import Path

CITIES_JS = re.compile(r"^\(window\.CP_CITIES = window\.CP_CITIES \|\| \{\}\)\.(\w+) = (\{.*\});\s*$", re.S)


def read_index(root):
    s = (Path(root) / "index.html").read_text(encoding="utf-8")
    i = s.index("const DATA=") + len("const DATA=")
    d, end = json.JSONDecoder().raw_decode(s[i:])
    return s, i, i + end, d


def read_cities(root):
    out = {}
    for f in sorted((Path(root) / "data").glob("cities-*.js")):
        m = CITIES_JS.match(f.read_text(encoding="utf-8"))
        if not m:
            raise ValueError(f"{f}: unexpected format")
        out.update(json.loads(m.group(2)))
    return out


def load_data(root):
    d = read_index(root)[3]
    if not d.get("cities"):
        d["cities"] = read_cities(root)
    return d
