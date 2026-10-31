"""Builds admin1/<cc>.json for the region mode (city -> click its region).

Usage: python tools/build_admin1.py <ne_10m_admin_1_states_provinces.geojson>
Needs: shapely (pip install shapely) and mapshaper (npm i -g mapshaper, or npx).

For each country of index.html (DATA.countries) with at least 3 units:
  sub = Natural Earth admin-1 units (states, provinces, départements…)
  reg = the same units dissolved on Natural Earth's `region` field (French régions, Italian regioni,
        Philippine regions…), kept only when it gives 3+ groups and fewer than `sub`
Each city of DATA.cities is attached to the unit that contains it (nearest unit within 25 km for
coastal points). Neighbouring units are listed so a near miss can earn partial points.
Output: admin1/<cc>.json = {v, levels: {sub|reg: {names, nb}}, city: {sub|reg: [unit index per city]}, topo}
and admin1/index.json = {cc: {sub: n, reg: n}}.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "admin1"
MS = shutil.which("mapshaper") or "npx mapshaper"
OWN_BUILD = {"ID"}   # built by tools/build_id.py (38 current provinces + kabupaten), not from Natural Earth

def ms(args):
    cmd = (MS + " " + args) if " " in MS else [MS] + args.split()
    subprocess.run(cmd, shell=isinstance(cmd, str), check=True, capture_output=True)

def load_data():
    s = (ROOT / "index.html").read_text(encoding="utf-8")
    d, _ = json.JSONDecoder().raw_decode(s[s.index('{"countries":{"AD"'):])
    return d

def main(ne_path):
    data = load_data()
    ne = json.loads(Path(ne_path).read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    index = {}
    tmp = Path(tempfile.mkdtemp())
    for cc in sorted(data["countries"]):
        if cc in OWN_BUILD:
            lv = json.loads((OUT / f"{cc}.json").read_text(encoding="utf-8"))["levels"]
            index[cc] = {k: len(lv[k]["names"]) for k in ("sub", "reg") if k in lv}
            continue
        feats = [f for f in ne["features"] if f["properties"].get("iso_a2") == cc
                 and "Overseas" not in (f["properties"].get("type_en") or "")]
        if len(feats) < 3: continue
        for f in feats:
            p = f["properties"]
            f["properties"] = {"name": p.get("name") or p.get("gn_name") or "?", "region": p.get("region") or ""}
        src = tmp / f"{cc}.geojson"
        src.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), encoding="utf-8")
        regions = {f["properties"]["region"] for f in feats}
        use_reg = "" not in regions and 3 <= len(regions) < len(feats)
        # simplify once on the topology (shared borders stay shared), then derive the region level
        ms(f"-i {src} -simplify 12% keep-shapes -clean -o {tmp/(cc+'_sub.geojson')} precision=0.0001")
        if use_reg:
            ms(f"-i {tmp/(cc+'_sub.geojson')} -dissolve region copy-fields=region -each name=region -o {tmp/(cc+'_reg.geojson')} precision=0.0001")
        levels, cities = {}, {}
        for lv in (["sub", "reg"] if use_reg else ["sub"]):
            fc = json.loads((tmp / f"{cc}_{lv}.geojson").read_text(encoding="utf-8"))
            fc["features"].sort(key=lambda f: f["properties"]["name"])
            for i, f in enumerate(fc["features"]): f["properties"] = {"i": i, "name": f["properties"]["name"]}
            (tmp / f"{cc}_{lv}.geojson").write_text(json.dumps(fc), encoding="utf-8")
            geoms = [shape(f["geometry"]).buffer(0) for f in fc["features"]]
            tree = STRtree(geoms)
            idx = []
            for c in data["cities"][cc]:
                pt = Point(c[2], c[1])
                hit = [int(j) for j in tree.query(pt, predicate="intersects")]
                if hit: idx.append(hit[0]); continue
                j = int(tree.nearest(pt))
                idx.append(j if geoms[j].distance(pt) < 0.25 else -1)   # ~25 km
            nb = []
            for i, g in enumerate(geoms):
                gb = g.buffer(0.002)
                nb.append(sorted(int(j) for j in tree.query(gb, predicate="intersects") if int(j) != i))
            levels[lv] = {"names": [f["properties"]["name"] for f in fc["features"]], "nb": nb}
            cities[lv] = idx
        topo = tmp / f"{cc}.topojson"
        files = " ".join(str(tmp / f"{cc}_{lv}.geojson") for lv in levels)
        ms(f"-i {files} combine-files -o format=topojson quantization=20000 {topo}")
        t = json.loads(topo.read_text(encoding="utf-8"))
        t["objects"] = {re.sub(r"^.*_(sub|reg)$", r"\1", k): v for k, v in t["objects"].items()}
        out = {"v": 1, "levels": levels, "city": cities, "topo": t}
        (OUT / f"{cc}.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        index[cc] = {lv: len(levels[lv]["names"]) for lv in levels}
        miss = sum(1 for v in cities["sub"] if v < 0)
        print(f"{cc}: sub {index[cc]['sub']}" + (f", reg {index[cc]['reg']}" if "reg" in index[cc] else "")
              + f", {(OUT/(cc+'.json')).stat().st_size//1024} KB" + (f", {miss} cities outside" if miss else ""))
    (OUT / "index.json").write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    shutil.rmtree(tmp)

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
