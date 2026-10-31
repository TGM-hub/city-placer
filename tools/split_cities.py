"""Move DATA.cities out of index.html into data/cities-<continent>.js (one file per continent).

    python tools/split_cities.py

index.html keeps the small part of DATA plus "ncities" (number of cities per country); the page loads a
continent file when a map needs it (country / continent: one file, world: all six). Script tags, not fetch,
so the page still opens with a double click (file://). Re-running is safe: if index.html still holds cities
(edited by hand), they replace the files; otherwise nothing changes.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cpdata import read_index  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    s, a, b, d = read_index(ROOT)
    if not d.get("cities"):
        print("index.html holds no cities: already split, nothing to do."); return
    by = defaultdict(dict)
    for cc, lst in d["cities"].items():
        by[d["continents"][cc]][cc] = lst
    (ROOT / "data").mkdir(exist_ok=True)
    for cont, part in sorted(by.items()):
        js = f"(window.CP_CITIES = window.CP_CITIES || {{}}).{cont} = " + json.dumps(part, ensure_ascii=False, separators=(",", ":")) + ";\n"
        (ROOT / "data" / f"cities-{cont}.js").write_text(js, encoding="utf-8", newline="\n")
        print(f"data/cities-{cont}.js  {len(part)} countries, {sum(map(len, part.values()))} cities, {len(js.encode()) // 1024} KB")
    d["ncities"] = {cc: len(lst) for cc, lst in d["cities"].items()}
    d["cities"] = {}
    s = s[:a] + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + s[b:]
    (ROOT / "index.html").write_text(s, encoding="utf-8", newline="")
    print(f"index.html {len(s.encode()) // 1024} KB")


if __name__ == "__main__":
    main()
