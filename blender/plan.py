"""Floor-plan data for the flat, shared by every Blender script.

All geometry is given in pixels of the listing floor plan (628x800 drawing), in the
orientation that matches the real flat (the listing drawing is mirrored left/right).
Plan x grows to the "east", plan y grows to the "south"; the windows face plan-north.

Blender world: X = east, Y = north, Z = up, metres.
glTF / three.js: x = east, y = up, z = south.

Scale: the plan has no scale bar. S = 0.0161 m/px is derived from three independent checks:
  * the half-room (félszoba) must be <= 12 m2 by Hungarian definition   -> S <= 0.0162
  * the bath tub runs wall to wall in the 94 px bathroom (150 cm tub)     -> S ~= 0.0160
  * prefab panel spans of 4.2 m / 5.4 m between wall axes of the big room -> S ~= 0.0161
"""

S = 0.0161          # metres per plan pixel
PX0, PY0 = 94, 54   # plan pixel that maps to the Blender origin (north-west corner)
H = 2.60            # clear ceiling height, typical for Hungarian panel buildings
SLAB = 0.20         # floor slab thickness used for the loggia roof


def X(px):
    return (px - PX0) * S


def Y(py):
    return -(py - PY0) * S


# Inner room rectangles (x0, y0, x1, y1) in plan pixels.
ROOMS = {
    'living':  dict(name='Living room', hu='szoba',    rects=[(268, 106, 519, 432)], floor='parquet'),
    'bedroom': dict(name='Bedroom',     hu='félszoba', rects=[(106, 138, 263, 432)], floor='parquet'),
    'kitchen': dict(name='Kitchen',     hu='konyha',   rects=[(106, 599, 266, 688)], floor='tile_floor'),
    'hall':    dict(name='Hall',        hu='előszoba', rects=[(106, 437, 356, 491), (263, 491, 356, 688)], floor='tile_floor'),
    'bath':    dict(name='Bathroom',    hu='fürdő',    rects=[(106, 497, 200, 592)], floor='tile_bath_floor'),
    'wc':      dict(name='WC',          hu='wc',       rects=[(207, 497, 256, 592)], floor='tile_floor'),
    'loggia':  dict(name='Loggia',      hu='loggia',   rects=[(106, 58, 263, 126)], floor='tile_loggia'),
}
ROOM_ORDER = ['living', 'kitchen', 'bedroom', 'hall', 'bath', 'wc', 'loggia']

# Full-height wall slabs (x0, y0, x1, y1) in plan pixels, openings are cut afterwards.
SLABS = [
    (94, 98, 106, 700),     # west outer wall
    (100, 54, 106, 126),    # loggia west side wall
    (263, 54, 268, 126),    # loggia east side wall
    (263, 98, 531, 106),    # living room north (window) wall
    (519, 98, 531, 443),    # living room east wall
    (94, 126, 268, 138),    # bedroom north (loggia) wall
    (263, 98, 268, 437),    # bedroom | living partition
    (94, 432, 263, 437),    # bedroom south wall
    (263, 432, 356, 437),   # living room south wall (interior part)
    (356, 432, 531, 443),   # living room south wall (exterior part)
    (356, 437, 367, 700),   # hall east outer wall
    (94, 688, 367, 700),    # south outer wall
    (94, 491, 263, 497),    # bath / wc north wall
    (200, 497, 207, 593),   # bath | wc partition
    (256, 491, 263, 599),   # wc east wall
    (94, 593, 272, 599),    # kitchen north wall
    (266, 593, 272, 688),   # kitchen east wall
]

# Openings. rect = cutter in plan px (spans the wall thickness), z = (bottom, top) in metres.
# hinge: which end of the gap carries the hinges ('a0' = min coordinate), swing: room the leaf opens into.
OPENINGS = [
    dict(id='door_living',  kind='door', axis='x', rect=(268, 428, 317, 447), z=(0, 2.05), wall=(432, 437),
         hinge='a0', swing='living', angle=80, leaf='flush'),
    dict(id='door_bedroom', kind='door', axis='x', rect=(169, 428, 218, 441), z=(0, 2.05), wall=(432, 437),
         hinge='a0', swing='bedroom', angle=78, leaf='glazed'),
    dict(id='door_bed_liv', kind='door', axis='y', rect=(259, 295, 272, 343), z=(0, 2.05), wall=(263, 268),
         hinge='a1', swing='bedroom', angle=0, leaf='flush'),     # kept closed: bookcase in front on the living side
    dict(id='door_bath',    kind='door', axis='x', rect=(134, 487, 173, 501), z=(0, 2.05), wall=(491, 497),
         hinge='a0', swing='hall', angle=96, leaf='vent'),
    dict(id='door_wc',      kind='door', axis='x', rect=(212, 487, 252, 501), z=(0, 2.05), wall=(491, 497),
         hinge='a0', swing='hall', angle=92, leaf='vent'),
    dict(id='door_kitchen', kind='arch', axis='y', rect=(262, 642, 276, 681), z=(0, 2.05), wall=(266, 272)),
    dict(id='door_front',   kind='door', axis='x', rect=(275, 684, 342, 704), z=(0, 2.08), wall=(688, 700),
         hinge='a1', swing='hall', angle=0, leaf='entry'),
    dict(id='door_balcony', kind='balcony', axis='x', rect=(206, 122, 255, 142), z=(0, 2.25), wall=(126, 138),
         hinge='a1', swing='bedroom', angle=72),
    dict(id='win_bedroom',  kind='window', axis='x', rect=(114, 122, 206, 142), z=(0.86, 2.25), wall=(126, 138), panes=1),
    dict(id='win_living',   kind='window', axis='x', rect=(351, 94, 443, 110), z=(0.86, 2.25), wall=(98, 106), panes=3),
    dict(id='win_kitchen',  kind='window', axis='x', rect=(141, 684, 234, 704), z=(0.95, 2.20), wall=(688, 700), panes=2),
]

# Walk-mode spawn points: plan px + yaw (radians, 0 = looking plan-north, + = turn left)
SPAWNS = {
    'living':  (300, 420, -0.75),
    'kitchen': (258, 662, 1.5708),
    'bedroom': (192, 404, 0.10),
    'hall':    (310, 668, 0.0),
    'bath':    (152, 500, 3.1416),
    'wc':      (231, 500, 3.1416),
    'loggia':  (180, 112, 0.0),
}


def room_area(key):
    return sum((r[2] - r[0]) * (r[3] - r[1]) for r in ROOMS[key]['rects']) * S * S


def net_area():
    return sum(room_area(k) for k in ROOMS if k != 'loggia')
