# River-view flat · 3D walkthrough

A walkable 3D model of a 1½-room flat (szoba + félszoba, loggia), reconstructed from the
listing floor plan and photos of the flat. Open it in a browser to orbit the whole flat,
walk through it at eye height, or read it as a plan.

## View it

The site is static. Serve the repository root over HTTP and open it:

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

It also works as-is on GitHub Pages (Settings → Pages → deploy from the branch root).

Controls in **Walk** mode: `W A S D` or arrow keys to move, drag to look, `Shift` to walk
faster, double-click to capture the mouse. On a phone: left thumb moves, the other thumb looks.
Click the mini map (or a spot in **Plan** mode) to jump there.

## How it is made

| Step | Script | Output |
|---|---|---|
| CC0 source textures and plant models | `blender/fetch_assets.sh` | `assets_src/` (not in git) |
| Walls, doors, windows, finishes and every furniture piece, modelled with Python in Blender 4.2 | `blender/build.py` (+ `plan.py`, `lib.py`, `furniture.py`, `textures.py`) | `build/flat.blend`, `data/scene.json` |
| Daylight + lamps baked into per-room lightmaps with Cycles, denoised with OIDN, exported to glTF | `blender/bake.py` | `assets/flat.glb`, `assets/lm_*.jpg` |
| The view out of the windows (river, far bank, hills) rendered as a panorama | `blender/panorama.py` | `assets/view.jpg` |
| Viewer | `index.html`, `app.js` (three.js r170, vendored) | |
| Optional: separate-file glTF + preview folder | `blender/export.py -- --separate`, `blender/make_preview.py` | `build/preview/` |

Rebuild everything:

```sh
blender/fetch_assets.sh
blender -b -P blender/build.py
blender -b build/flat.blend -P blender/bake.py -- --samples 128
blender -b -P blender/panorama.py
```

`blender/render_test.py` renders Cycles check images of each room into `build/renders/`.

## Accuracy notes

* **Scale.** The listing plan has no scale bar. The scale (1.61 cm per plan pixel) comes from three
  independent checks: the half-room must be at most 12 m², the bath tub runs wall to wall in a
  150 cm bathroom, and the big room's wall axes match the 4.2 m / 5.4 m spans of panel buildings.
  That gives about 48.6 m² net. If the real floor area is known, change `S` in `blender/plan.py`
  and rebuild.
* **Orientation.** The listing drawing is a mirror image of the real flat (checked against the
  photos: the kitchen opening, the door hinges and the living-room door corner). The model follows
  the real flat.
* **Furniture** follows the photos and the catalogue sizes of the pieces (IKEA FRIHETEN sofa,
  LACK table, POÄNG chair, BILLY bookcase, HEMNES day-bed, TARVA and IVAR pine pieces, RIGGA rack, RÅSKOG trolley).
  Small clutter is left out on purpose.
* The bedroom–living room door is modelled closed: in the photos the bookcase stands in front of it.
* The balcony door is shown open so you can step out onto the loggia in Walk mode.
* The view out of the windows is a stylised reconstruction, not a photograph.

Textures: [ambientCG](https://ambientcg.com) (CC0). Plants and vases: [Poly Haven](https://polyhaven.com) (CC0).
