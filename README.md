# Flat portfolio · 3D walkthroughs

Walkable 3D models of two flats, reconstructed from their floor plans and photos. Open the site,
pick a flat from the **Portfolio** tabs, and orbit the whole flat, walk through it at eye height,
or read it as a plan.

| Tab | Flat | Source |
|---|---|---|
| River-view flat | 1½-room panel flat with a loggia, 48.6 m² | listing floor plan + photos |
| Garden flat | 3 rooms on the raised ground floor, 66.2 m², windows onto a garden | architect's plan (Grundplan, cm) + photos |

Links go straight to a flat and a mode: `#garden`, `#riverview.walk`, `#garden.plan`.

## View it

The site is static. Serve the repository root over HTTP and open it:

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

It deploys as-is on Vercel (`vercel.json`) or GitHub Pages (deploy from the branch root).

Controls in **Walk** mode: `W A S D` or arrow keys to move, drag to look, `Shift` to walk
faster, double-click to capture the mouse. On a phone: left thumb moves, the other thumb looks.
Click the mini map (or a spot in **Plan** mode) to jump there.

## How it is made

Each flat is one Python module in `blender/flats/` (rooms, walls, openings, spawn points, finishes,
lighting and a `furnish()` function that places every piece). `FLAT=<id>` picks the flat for
every script; outputs go to `build/<id>/`, `assets/<id>/` and `data/<id>.json`.
`data/flats.json` lists the tabs.

| Step | Script | Output |
|---|---|---|
| CC0 source textures and plant models | `blender/fetch_assets.sh` | `assets_src/` (not in git) |
| Walls, doors, windows, finishes and every furniture piece, modelled with Python in Blender 4.2 | `blender/build.py` (+ `flats/<id>.py`, `lib.py`, `furniture.py`, `furniture2.py`, `textures.py`) | `build/<id>/flat.blend`, `data/<id>.json` |
| Daylight + lamps baked into per-room lightmaps with Cycles, denoised with OIDN, exported to glTF | `blender/bake.py` | `assets/<id>/flat.glb`, `assets/<id>/lm_*.jpg` |
| The view out of the windows, rendered as a panorama | `blender/panorama.py` (river), `blender/flats/garden_view.py` (garden) | `assets/<id>/view.jpg` |
| Viewer | `index.html`, `app.js` (three.js r170, vendored) | |

Rebuild a flat:

```sh
blender/fetch_assets.sh
FLAT=garden blender -b -P blender/build.py
FLAT=garden blender -b build/garden/flat.blend -P blender/bake.py -- --samples 192
blender -b -P blender/flats/garden_view.py
```

`FLAT=<id> blender -b build/<id>/flat.blend -P blender/render_test.py` renders Cycles check
images of each room into `build/<id>/renders/`.

## Accuracy notes

### River-view flat

* **Scale.** The listing plan has no scale bar. The scale (1.61 cm per plan pixel) comes from three
  independent checks: the half-room must be at most 12 m², the bath tub runs wall to wall in a
  150 cm bathroom, and the big room's wall axes match the 4.2 m / 5.4 m spans of panel buildings.
  That gives about 48.6 m² net. If the real floor area is known, change `S` in
  `blender/flats/riverview.py` and rebuild.
* **Orientation.** The listing drawing is a mirror image of the real flat (checked against the
  photos: the kitchen opening, the door hinges and the living-room door corner). The model follows
  the real flat.
* **Furniture** follows the photos and the catalogue sizes of the pieces (IKEA FRIHETEN sofa,
  LACK table, POÄNG chair, BILLY bookcase, HEMNES day-bed, TARVA and IVAR pine pieces, RIGGA rack, RÅSKOG trolley).
  Small clutter is left out on purpose.
* The bedroom–living room door is modelled closed: in the photos the bookcase stands in front of it.
* The balcony door is shown open so you can step out onto the loggia in Walk mode.

### Garden flat

* **Dimensions** come straight from the architect's plan, which is drawn in centimetres. The room
  areas add up to 66.2 m², matching the plan's total (66.19 m²); ceiling height is about 2.95 m.
* **Furniture** follows the photos: the spruce shelving wall, the corner sofa and the wall clock in
  the living room, the floor bed in the west room, the sofa bed, desks and wardrobe in the east room,
  the galley kitchen with its red glass splashback, the loft storage in the walk-in closet.
* The garden door in the living room is shown closed; the other doors stand open.

The views out of the windows are stylised reconstructions, not photographs.

Textures: [ambientCG](https://ambientcg.com) (CC0). Plants and vases: [Poly Haven](https://polyhaven.com) (CC0).
