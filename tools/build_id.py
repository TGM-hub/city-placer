"""Builds admin1/ID.json from the indonesia-kabupaten repo (38 current provinces + 514 kabupaten/kota),
replacing Natural Earth's 33 pre-2022 provinces. build_admin1.py skips ID so this file is not overwritten.

Usage: python tools/build_id.py [path to the indonesia-kabupaten repo]   (default: ../indonesia-kabupaten)
Needs: shapely (pip install shapely) and mapshaper (npm i -g mapshaper, or npx).

Levels: reg = island groups (Sumatra, Java, Kalimantan…), sub = provinces, kab = kabupaten + kota.
Same output format as build_admin1.py: {v, levels: {lv: {names, nb}}, city: {lv: [unit per city]}, topo}.
Sources: geoBoundaries IDN ADM2 (CC BY 3.0 IGO), names and codes from cahyadsn/wilayah (MIT), see that repo.
"""
import csv, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent
MS = shutil.which("mapshaper") or "npx mapshaper"

def ms(args):
    cmd = (MS + " " + args) if " " in MS else [MS] + args.split()
    subprocess.run(cmd, shell=isinstance(cmd, str), check=True, capture_output=True)

def load_data():
    s = (ROOT / "index.html").read_text(encoding="utf-8")
    d, _ = json.JSONDecoder().raw_decode(s[s.index('{"countries":{"AD"'):])
    return d

def main(src):
    src = Path(src)
    rows = list(csv.DictReader((src / "data/kabupaten.csv").open(encoding="utf-8")))
    shapes = json.loads((src / "data/shapes.json").read_text(encoding="utf-8"))
    island = {r["province_code"]: r["island"] for r in rows}
    pname = {r["province_code"]: r["province"] for r in rows}
    kab = [{"type": "Feature", "properties": {"name": ("Kota " if r["type"] == "kota" else "Kab. ") + r["name"],
            "prov": r["province_code"]}, "geometry": {"type": "MultiPolygon", "coordinates": shapes[r["code"]]["poly"]}}
           for r in rows if r["code"] in shapes]
    missing = [r["code"] for r in rows if r["code"] not in shapes]
    if missing: print("no shape for", missing)
    tmp = Path(tempfile.mkdtemp())
    (tmp / "kab_in.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": kab}), encoding="utf-8")
    ms(f"-i {tmp/'kab_in.geojson'} snap -simplify 60% keep-shapes -clean -o {tmp/'ID_kab.geojson'} precision=0.0001")
    # provinces and islands dissolved from the kabupaten, so all three levels share their borders
    fc = json.loads((tmp / "ID_kab.geojson").read_text(encoding="utf-8"))
    for f in fc["features"]:
        p = f["properties"]["prov"]; f["properties"].update(pname=pname[p], island=island[p])
    (tmp / "ID_kab.geojson").write_text(json.dumps(fc), encoding="utf-8")
    ms(f"-i {tmp/'ID_kab.geojson'} -dissolve pname -each name=pname -o {tmp/'ID_sub.geojson'} precision=0.0001")
    ms(f"-i {tmp/'ID_kab.geojson'} -dissolve island -each name=island -o {tmp/'ID_reg.geojson'} precision=0.0001")
    cities = load_data()["cities"]["ID"]
    levels, cmap = {}, {}
    for lv in ("reg", "sub", "kab"):
        fc = json.loads((tmp / f"ID_{lv}.geojson").read_text(encoding="utf-8"))
        fc["features"].sort(key=lambda f: f["properties"]["name"])
        for i, f in enumerate(fc["features"]): f["properties"] = {"i": i, "name": f["properties"]["name"]}
        (tmp / f"ID_{lv}.geojson").write_text(json.dumps(fc), encoding="utf-8")
        geoms = [shape(f["geometry"]).buffer(0) for f in fc["features"]]
        tree = STRtree(geoms)
        idx = []
        for c in cities:
            pt = Point(c[2], c[1])
            hit = [int(j) for j in tree.query(pt, predicate="intersects")]
            if hit: idx.append(hit[0]); continue
            j = int(tree.nearest(pt))
            idx.append(j if geoms[j].distance(pt) < 0.25 else -1)   # ~25 km
        nb = [sorted(int(j) for j in tree.query(g.buffer(0.002), predicate="intersects") if int(j) != i) for i, g in enumerate(geoms)]
        levels[lv] = {"names": [f["properties"]["name"] for f in fc["features"]], "nb": nb}
        cmap[lv] = idx
    topo = tmp / "ID.topojson"
    ms(f"-i {tmp/'ID_reg.geojson'} {tmp/'ID_sub.geojson'} {tmp/'ID_kab.geojson'} combine-files -o format=topojson quantization=20000 {topo}")
    t = json.loads(topo.read_text(encoding="utf-8"))
    t["objects"] = {k.split("_")[-1]: v for k, v in t["objects"].items()}
    out = ROOT / "admin1" / "ID.json"
    out.write_text(json.dumps({"v": 1, "levels": levels, "city": cmap, "topo": t}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"ID: reg {len(levels['reg']['names'])}, sub {len(levels['sub']['names'])}, kab {len(levels['kab']['names'])}, "
          f"{out.stat().st_size//1024} KB, {sum(1 for v in cmap['sub'] if v < 0)} cities outside")
    shutil.rmtree(tmp)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "indonesia-kabupaten")
