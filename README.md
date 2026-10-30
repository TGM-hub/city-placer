# City Placer

GeoGuessr trainer for placing cities on a blank map, limited to the 111 countries and territories covered by GeoGuessr. Inspired by [sharkdp/quizzity](https://github.com/sharkdp/quizzity).

Live: https://tgm-hub.github.io/city-placer/

## How it works

Pick a map, a pool size and a mode, then play rounds of 5, 10, 20 cities or endless.

| Mode | Question | Answer |
|---|---|---|
| Name → place it | `Clermont-Ferrand` | click the map |
| Pin → type the name | a pin on the map | type the city (accent-insensitive autocomplete) |
| Name → click its region | `Clermont-Ferrand` | click its region (single-country maps only) |

**Maps**
- One country: the pool is set by a population threshold (≥ 5k … ≥ 1M); the default keeps about 120 cities.
- Multi-country: GeoGuessr world or one continent. The pool is the top N cities per country (fewer for small countries, one for micro-territories, which can be skipped in the settings). A country is drawn first, then a city, so big countries don't crowd out the rest.

**Country frequency** (world and continent maps): each country has a GeoGuessr frequency tier (Common, Regular, Rare, Very rare). A country is drawn with odds = tier weight × how weak you are there. Defaults: Common ×4, Regular ×2, Rare ×1, Very rare off; rare countries keep only their 3 biggest cities. Everything is editable in Settings (⚙): weight per tier, cities kept in rare countries, and the tier of any country. Single-country maps are not affected.

**Region mode**: the country's states, provinces or départements are outlined; click the one the city is in.
Right region 5,000 pts, a neighbouring region 2,000, anything else 0. Where Natural Earth groups units into larger
regions (French régions, Italian regioni, Philippine regions, Spanish comunidades…), a selector switches between
**Large regions** and **Subdivisions**. Progress is tracked separately per level.

**Scoring**: GeoGuessr-style, `5000 · e^(−10·d / D)`, where `D` is the size of the map (the country's diagonal, or the GeoGuessr world map value for the world).

**After each answer**: distance, score, region of the city, population, a satellite close-up, and place names on the Roads basemap (hidden while you guess).

**Hints** (`H` or `?`): continent → country → north/south/east/west → region in place mode; country → region → blanks with letter count → first three letters in name mode. Each hint lowers the max score (×0.85, ×0.65, ×0.5, ×0.35).

**Spaced repetition**: each city sits in a Leitner box (0–5). Weak and unseen cities come up more often; box 4+ counts as mastered (progress bar). Place and name modes are tracked separately.

**Weak spots**: the 20 cities averaging under 4,000 points, your mean offset (e.g. "40 km north, 15 km west"), your misses on the map, and a "Drill these" round.

**Settings (⚙)**: basemap (Roads, Gray, Satellite, Relief, Borders only), place names after answers, satellite close-up, wheel zoom speed, micro-territories, reset progress for the current pool.

Keys: `Space`/`Enter` next · `H`/`?` hint · `Esc` close panel · `↑ ↓ Enter` in the name suggestions.

Progress and preferences are stored in the browser (`localStorage`, keys `cp.srs` and `cp.prefs`).

## Files

```
index.html   the whole app: UI, city data, country shapes (about 2.3 MB, no build step)
admin1/      region outlines per country, loaded on demand by the region mode (generated)
tools/build_admin1.py  regenerates admin1/ from Natural Earth admin-1 (needs shapely + mapshaper)
```

Runtime network: MapLibre GL (jsDelivr) and the basemap tiles. The "Borders only" basemap needs no tiles.

## Sources and licences

- Cities, populations and regions: [GeoNames](https://www.geonames.org), CC BY 4.0.
- Country borders and admin-1 regions: [Natural Earth](https://www.naturalearthdata.com), public domain.
- Basemaps: [OpenFreeMap](https://openfreemap.org) (OpenStreetMap data, ODbL), Esri tiles (World Imagery, Light/Dark Gray Canvas, Shaded Relief).
- Libraries: [MapLibre GL JS](https://maplibre.org) (BSD-3), [topojson-client](https://github.com/topojson/topojson-client) (ISC).
