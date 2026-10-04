"""River-view flat (1½ rooms + loggia, panel building). Plan data, furnishing and lighting.

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
    return sum(room_area(k) for k in ROOMS if k not in OUTDOOR)


# ---------------------------------------------------------------- flat specific build settings
ID = 'riverview'
META = dict(
    title='River-view flat',
    eyebrow='Panel flat · 1½ rooms',
    lede='1½ rooms on a high floor of a panel building, with a loggia over the river and the hills.',
    stats=[['48.6', 'm²', 'Interior, estimated'], ['2.60', 'm', 'Ceiling height'], ['2.8', 'm²', 'Loggia'],
           ['1½', '', 'Rooms (szoba + félszoba)']],
    note='Room sizes are measured from the listing floor plan. The plan has no scale bar, so sizes may be off by a few percent.',
)
OUTDOOR = ('loggia',)                      # rooms without ceiling, facade-coloured walls, not counted in the area
BOUNDS_PX = (94, 54, 531, 700)             # outline used by the viewer (mini map, plan camera)
EXTRA_COLLIDERS_PX = [(100, 54, 268, 58)]  # loggia railing
SILL_TILE_ROOMS = ('kitchen',)
SKIRTING = [('living', 'wood_skirting', 0.06), ('bedroom', 'wood_skirting', 0.06), ('hall', 'tile_floor', 0.08),
            ('loggia', 'tile_loggia', 0.08)]
CLADDING = [('kitchen', 1.50, 'tile_kitchen', {}), ('bath', 2.00, 'tile_bath', {}),
            ('wc', 1.50, 'tile_wc', dict(band=(1.40, 1.50)))]
# ceiling fill lights: room -> [(px, py, size_x, size_y, watts)]
FILLS = {
    'living': [((268 + 519) / 2, (106 + 432) / 2, 2.8, 3.6, 18)],
    'bedroom': [((106 + 263) / 2, (138 + 432) / 2, 1.6, 3.2, 12)],
    'kitchen': [((106 + 266) / 2, (599 + 688) / 2, 1.6, 0.9, 30)],
    'hall': [((106 + 356) / 2, (437 + 491) / 2, 2.6, 0.5, 26), ((263 + 356) / 2, (491 + 688) / 2, 0.9, 2.4, 40)],
    'bath': [((106 + 200) / 2, (497 + 592) / 2, 0.8, 0.8, 26)],
    'wc': [((207 + 256) / 2, (497 + 592) / 2, 0.4, 0.8, 12)],
}
SUN = dict(elevation=26, azimuth=-6, energy=45.0)   # azimuth 0 = from plan-north (+Y)
VIEW_ROTATION = 1.5708                              # panorama yaw in the viewer
VIEWS = {
    'living_b': (500, 130, 2.45, 1.60, -0.05),
    'living_c': (300, 140, -2.35, 1.55, -0.05),
    'bedroom_b': (150, 160, 3.14, 1.60, -0.08),
    'hall_b': (300, 455, -1.0, 1.60, -0.05),
    'kitchen_b': (120, 650, -1.5708, 1.55, -0.12),
    'win_close': (397, 160, 0.0, 1.45, 0.0),
}


def extra_arch(b):
    """Loggia: the slab above (its underside is the loggia ceiling) and the slab below."""
    xa, ya, xb, yb = b.rect_m((100, 54, 268, 126))
    g = b.Geo()
    g.add(b.quad(X(106), Y(126), X(263), Y(58), H, up=False), b.M['facade'], jitter=False)
    g.add(b.box_ext(xa, ya, H, xb, yb, H + SLAB), b.M['concrete'])
    g.add(b.box_ext(xa, ya, -SLAB, xb, yb, -0.002), b.M['concrete'])
    b.make('loggia_slabs', g, collection='arch', room='loggia', smooth=None, props={'kind': 'ceiling'})


def furnish(b):
    """Place every piece of furniture. `b` is the build module namespace (place, F, M, R, ...)."""
    globals().update({k: v for k, v in vars(b).items() if not k.startswith("__")})
    # ---------------- living room (4.04 x 5.25 m)
    L = 'living'
    lw, ld = (519 - 268) * S, (432 - 106) * S
    place(F.sofa_friheten(), 'sofa', L, lw - 0.46, 1.60, 'W', solid=True)
    place(F.lack_table(), 'coffee_table', L, 2.42, 2.18, rz=pi / 2, solid=True)
    place(F.rug(1.6, 2.3, 'rug_living'), 'rug_living', L, 2.55, 2.18, rz=0)
    fit_uv(bpy.data.objects['rug_living'], 'xy')
    place(F.not_lamp(), 'floor_lamp', L, lw - 0.24, 2.95, 'W')
    place(F.poster_frame(), 'poster', L, lw - 0.006, 2.15, 'W', z=1.25)
    fit_uv(bpy.data.objects['poster'], 'xz', flip_u=False)
    place(F.ac_unit(), 'ac_living', L, lw - 0.11, 0.70, 'W', z=2.06)
    place(F.radiator(0.8), 'radiator_living', L, 1.75, 0.07, 'S', z=0.12)
    place(F.curtain_rod(2.05), 'rod_living', L, 2.08, 0.11, 'S', z=2.40)
    place(F.curtain(0.48, 2.32), 'curtain_living_l', L, 1.30, 0.12, 'S', z=0.05)
    place(F.curtain(0.48, 2.32), 'curtain_living_r', L, 2.86, 0.12, 'S', z=0.05)
    place(F.poang(), 'armchair', L, 0.55, 0.72, rz=pi / 4, solid=True)
    place(F.bamboo_shelf(), 'bamboo_shelf', L, 2.36, 0.22, 'S', solid=True)
    place(F.billy(), 'bookcase', L, 0.175, 3.95, 'E', solid=True)
    place(F.dark_cabinet(), 'cabinet_dark', L, 0.21, 3.18, 'E', solid=True)
    place(F.cube_shelf(), 'cube_shelf', L, 1.42, ld - 0.57, 'W', solid=True)
    place(F.dining_table(1.05), 'dining_table', L, 3.05, 4.25, solid=True)
    place(F.sled_chair(), 'chair_1', L, 3.05, 3.50, 'S')
    place(F.sled_chair(), 'chair_2', L, 2.28, 4.25, 'E')
    place(F.folding_chair(), 'chair_3', L, 3.05, 5.00, 'N')
    place(F.drum_pendant(0.72), 'pendant_living', L, 2.15, 2.75, z=H)
    x, y = R(L, 0.38, 1.50)
    place(F.pot(0.17, 0.30, 'terracotta'), 'pot_pachira', L, 0.38, 1.50)
    import_model('pachira_aquatica_01', 'plant_pachira', L, (x, y, 0.27), rz=0.6, height=1.25, keep=['_b'])
    x, y = R(L, 0.31, 3.18)      # kept off the wall: the closed bedroom door is right behind the cabinet
    import_model('potted_plant_02', 'plant_cabinet', L, (x, y, 0.95), rz=1.2, height=0.62)
    x, y = R(L, 1.30, ld - 0.70)
    import_model('ceramic_vase_01', 'vase_shelf', L, (x, y, 1.12), height=0.24)

    # ---------------- bedroom (2.53 x 4.73 m)
    B = 'bedroom'
    bw, bd = (263 - 106) * S, (432 - 138) * S
    place(F.desk(), 'desk', B, 0.95, 0.45, 'S', solid=True)
    place(F.slat_chair(), 'desk_chair', B, 0.95, 1.05, 'N')
    place(F.drawers(0.48, 0.40, 0.70, 3), 'nightstand', B, 0.205, 1.06, 'E', solid=True)
    place(F.daybed_hemnes(), 'daybed', B, 0.855, 2.40, 'E', solid=True)
    place(F.sideboard(), 'sideboard', B, 0.205, 3.95, 'E', solid=True)
    place(F.towel_ladder(), 'towel_ladder', B, 0.10, 4.50, 'E')
    place(F.drawers(0.79, 0.43, 1.10, 5), 'chest_tarva', B, bw - 0.218, 1.95, 'W', solid=True)
    place(F.ivar(), 'shelf_ivar', B, bw - 0.152, 1.04, 'W', solid=True)
    place(F.ac_unit(), 'ac_bedroom', B, bw - 0.11, 1.95, 'W', z=2.08)
    place(F.rigga(), 'clothes_rack', B, bw - 0.27, 4.12, rz=pi / 2, solid=True)
    place(F.lantern(0.62), 'lantern', B, 1.26, 2.45, z=H)
    place(F.not_lamp('metal_grey'), 'floor_lamp_bed', B, 0.16, 0.66, 'S')
    place(F.radiator(1.0), 'radiator_bedroom', B, 0.87, 0.07, 'S', z=0.12)
    place(F.curtain_rod(2.45), 'rod_bedroom', B, 1.26, 0.11, 'S', z=2.40)
    place(F.curtain(0.40, 2.32), 'curtain_bed_l', B, 0.23, 0.12, 'S', z=0.05)
    place(F.curtain(0.30, 2.32), 'curtain_bed_r', B, 2.38, 0.12, 'S', z=0.05)
    x, y = R(B, bw - 0.152, 1.04)
    place(F.pot(0.10, 0.14, 'ceramic_white'), 'pot_ivar', B, bw - 0.152, 1.04, z=1.79)
    import_model('calathea_orbifolia_01', 'plant_ivar', B, (x, y, 1.91), height=0.36, keep=['_b'])
    x, y = R(B, 0.20, 3.82)
    import_model('ceramic_vase_03', 'vase_sideboard', B, (x, y, 0.90), height=0.22)

    # ---------------- kitchen (2.58 x 1.43 m)
    K = 'kitchen'
    kw, kd = (266 - 106) * S, (688 - 599) * S
    place(F.fridge(), 'fridge', K, 0.30, 0.30, 'S', solid=True)
    place(F.raskog(), 'trolley', K, 0.80, 0.25, 'S', solid=True)
    place(F.cooker(), 'cooker', K, 1.25, 0.31, 'S', solid=True)
    cw = kw - 1.51
    place(F.base_cabinets(cw, 2, sink_at=0.12), 'counter', K, 1.51 + cw / 2, 0.30, 'S', solid=True)
    place(F.wall_cabinets(kw - 1.0, ['open', 'glass', 'wood', 'wood']), 'wall_cabinets', K, 1.0 + (kw - 1.0) / 2, 0.165, 'S', z=1.48)
    place(F.fold_table(), 'fold_table', K, 1.55, kd - 0.20, 'N')
    place(F.wall_sconce(), 'sconce_kitchen', K, 0.01, 0.75, 'E', z=2.12)
    x, y = R(K, 0.95, kd + 0.02)
    import_model('potted_plant_04', 'plant_kitchen', K, (x, y, 0.955), height=0.22, drop=['ground'])

    # ---------------- bathroom (1.51 x 1.53 m)
    Bt = 'bath'
    tw, tdp = (200 - 106) * S, (592 - 497) * S
    place(F.bathtub(tw, 0.70, 0.55), 'bathtub', Bt, tw / 2, tdp - 0.35, 'S', solid=True)
    place(F.shower_mixer(), 'shower_mixer', Bt, 1.05, tdp, 'N', z=0.78)
    g = Geo()
    g.add(cyl(0.012, tw, at=(-tw / 2, 0, 0), seg=12, axis='X'), M['chrome'])
    place(g, 'curtain_rod_bath', Bt, tw / 2, tdp - 0.70, z=2.0)
    cg = F.curtain(0.42, 1.40, folds=5, amp=0.03)
    for mi, m_ in enumerate(cg.mats):
        cg.mats[mi] = M['curtain_floral']
    ob = place(cg, 'curtain_bath', Bt, 0.24, tdp - 0.70, 'S', z=0.58)
    fit_uv(ob, 'xz')
    place(F.wall_shelf(0.40, 0.15), 'shelf_bath', Bt, tw - 0.08, 1.15, 'W', z=1.55)
    x, y = R(Bt, tw - 0.08, 1.10)
    import_model('potted_plant_04', 'plant_bath', Bt, (x, y, 1.575), height=0.18, drop=['ground'])
    place(F.basket(), 'laundry_basket', Bt, tw - 0.24, 0.32, solid=True)
    place(F.flush_light(), 'light_bath', Bt, tw / 2, tdp / 2, z=H)

    # ---------------- WC (0.79 x 1.53 m)
    Wc = 'wc'
    ww, wd = (256 - 207) * S, (592 - 497) * S
    g = Geo()
    g.add(box(ww, 0.20, 1.05, bevel=0.004), M['wood_pine'], grain=0)
    g.add(box(0.24, 0.012, 0.16, at=(0.08, -0.105, 0.82), bevel=0.004), M['plastic_white'])
    g.add(box(0.07, 0.006, 0.10, at=(0.04, -0.113, 0.85), bevel=0.003), M['chrome'])
    g.add(box(0.07, 0.006, 0.10, at=(0.12, -0.113, 0.85), bevel=0.003), M['chrome'])
    place(g, 'cistern_box', Wc, ww / 2, wd - 0.10, 'S', solid=True)
    place(F.toilet(), 'toilet', Wc, 0.48, wd - 0.20, 'N', solid=True)
    place(F.wc_basin(), 'wc_basin', Wc, 0.135, 0.92, 'E', z=0.72, solid=True)
    place(F.paper_stand(), 'paper_stand', Wc, 0.12, 1.24, 'E')
    place(F.flush_light(0.13), 'light_wc', Wc, ww / 2, 0.6, z=H)

    # ---------------- hall
    Hl = 'hall'
    ex = 356
    place_px(F.built_in_cabinet(1.38, 0.40, H - 0.02), 'hall_cabinet', Hl, ex - 0.20 / S, 643, 'W', solid=True)
    place_px(F.open_shelf(0.80, 0.35, 1.0), 'hall_shelf', Hl, ex - 0.176 / S, 562, 'W', solid=True)
    place_px(F.paneling(1.42, 2.0), 'hall_paneling', Hl, ex - 0.008 / S, 488, 'W')
    place_px(F.overhead_cabinet(1.42, 0.36, 0.55), 'hall_overhead', Hl, ex - 0.20 / S, 488, 'W', z=2.03)
    place_px(F.coat_rack(1.0), 'coat_rack', Hl, 263 + 0.013 / S, 548, 'E', z=1.62)
    ob = place_px(F.rug(0.75, 1.9, 'rug_hall'), 'rug_hall', Hl, 309.5, 588)
    fit_uv(ob, 'xy')
    g = Geo()
    g.add(box(0.62, 0.42, 0.012, bevel=0.003), M['coir'])
    place_px(g, 'door_mat', Hl, 309, 672)
    place_px(F.dome_pendant(0.55), 'pendant_hall', Hl, 309.5, 585, z=H)
    place_px(F.brass_sconce(), 'sconce_hall', Hl, 106 + 0.01 / S, 464, 'E', z=2.05)
    place_px(F.flush_light(0.14), 'light_hall_a', Hl, 215, 464, z=H)

    # ---------------- loggia
    Lg = 'loggia'
    place_px(F.railing((263 - 106) * S), 'railing', Lg, (106 + 263) / 2, 56.5, 'S')
