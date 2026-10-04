"""Garden flat: 3 rooms on the raised ground floor of an older building, windows facing the garden.

Source: the architect's plan (Grundplan, dimensions in cm) plus photos of the furnished flat.
Plan units here are centimetres: x grows east, y grows south, origin at the inner north-west
corner of the walk-in closet. The garden (and all windows) are on the south side.

Room sizes from the plan's dimension chains, checked against the areas printed on it:
  living (Wohnzimmer) 405 x 472 = 19.12 m2   bedroom (Zimmer) 250 x 472 = 11.80 m2
  study (Zimmer)      332 x 382 = 12.68 m2   kitchen (Küche)  191 x 245 =  4.68 m2
  bathroom (Bad)      187 x 232 =  4.34 m2   WC               205 x 107 =  2.19 m2
  closet (Schrankraum) 280 x 107 = 3.00 m2   hall (Vorraum)   8.42 m2
  total 66.2 m2, which matches the plan's own net figure of 66.19 m2.
"""
from math import pi

S = 0.01            # metres per plan unit (cm)
PX0, PY0 = 0, 0
H = 2.95            # clear ceiling height (plan: stucco at 2.75 in the hall strip, beams at 3.00 in the rooms)


def X(px):
    return (px - PX0) * S


def Y(py):
    return -(py - PY0) * S


ROOMS = {
    'living':  dict(name='Living room',    hu='Wohnzimmer',  rects=[(260, 152, 665, 624)], floor='laminate'),
    'kitchen': dict(name='Kitchen',        hu='Küche',       rects=[(675, 379, 866, 624)], floor='laminate'),
    'bedroom': dict(name='Bedroom',        hu='Zimmer',      rects=[(0, 152, 250, 624)], floor='laminate'),
    'study':   dict(name='Study',          hu='Zimmer',      rects=[(876, 242, 1208, 624)], floor='laminate'),
    'closet':  dict(name='Walk-in closet', hu='Schrankraum', rects=[(0, 0, 280, 107)], floor='laminate'),
    'hall':    dict(name='Hall',           hu='Vorraum',     rects=[(546, 0, 866, 107), (675, 107, 866, 369)], floor='laminate'),
    'bath':    dict(name='Bathroom',       hu='Bad',         rects=[(876, 0, 1063, 232)], floor='tile_grey_floor'),
    'wc':      dict(name='WC',             hu='WC',          rects=[(329, 0, 534, 107)], floor='tile_grey_floor'),
}
ROOM_ORDER = ['living', 'kitchen', 'bedroom', 'study', 'closet', 'hall', 'bath', 'wc']

SLABS = [
    (-65, -25, 0, 666),       # west outer wall (40 cm brick + 25 cm lining)
    (-65, -25, 1248, 0),      # north wall to the building's stair hall
    (1208, -25, 1248, 666),   # east wall
    (-65, 624, 1248, 666),    # south facade to the garden (42 cm)
    (0, 107, 675, 152),       # 45 cm bearing wall between the closet/WC strip and the rooms
    (250, 152, 260, 624),     # bedroom | living
    (665, 152, 675, 624),     # living | hall + kitchen
    (866, 0, 876, 624),       # hall + kitchen | bath + study
    (675, 369, 866, 379),     # hall | kitchen
    (876, 232, 1208, 242),    # bath | study
    (1063, 0, 1208, 232),     # storeroom (not part of the flat) and chimney flues
    (280, 0, 329, 107),       # closet | WC (installation shaft for the wall-hung WC)
    (534, 0, 546, 107),       # WC | hall
]

OPENINGS = [
    dict(id='door_front', kind='door', axis='x', rect=(686, -29, 776, 4), z=(0, 2.08), wall=(-25, 0),
         hinge='a1', swing='hall', angle=0, leaf='entry'),
    dict(id='arch_closet', kind='arch', axis='x', rect=(103, 103, 203, 156), z=(0, 2.14), wall=(107, 152)),
    dict(id='door_wc', kind='door', axis='y', rect=(530, 18, 550, 88), z=(0, 2.0), wall=(534, 546),
         hinge='a0', swing='wc', angle=80, leaf='flush'),
    dict(id='door_bath', kind='door', axis='y', rect=(862, 15, 880, 85), z=(0, 2.0), wall=(866, 876),
         hinge='a1', swing='bath', angle=172, leaf='flush'),   # folded back against the wall
    dict(id='door_bedroom', kind='door', axis='y', rect=(246, 210, 264, 290), z=(0, 2.05), wall=(250, 260),
         hinge='a0', swing='bedroom', angle=82, leaf='flush'),
    dict(id='door_living', kind='door', axis='y', rect=(661, 220, 679, 300), z=(0, 2.05), wall=(665, 675),
         hinge='a0', swing='living', angle=86, leaf='flush'),
    dict(id='door_study', kind='door', axis='y', rect=(862, 289, 880, 369), z=(0, 2.05), wall=(866, 876),
         hinge='a1', swing='study', angle=80, leaf='flush'),
    dict(id='arch_kitchen', kind='arch', axis='y', rect=(661, 395, 679, 475), z=(0, 2.0), wall=(665, 675)),
    dict(id='door_garden', kind='balcony', axis='x', rect=(538, 620, 660, 670), z=(0, 2.25), wall=(624, 666),
         hinge='a1', swing='living', angle=0),
    dict(id='win_living', kind='window', axis='x', rect=(303, 620, 423, 670), z=(0.85, 2.80), wall=(624, 666), panes=2),
    dict(id='win_bedroom', kind='window', axis='x', rect=(100, 620, 220, 670), z=(0.85, 2.80), wall=(624, 666), panes=2),
    dict(id='win_kitchen', kind='window', axis='x', rect=(696, 620, 762, 670), z=(0.90, 2.85), wall=(624, 666), panes=1),
    dict(id='win_study', kind='window', axis='x', rect=(960, 620, 1077, 670), z=(0.85, 2.80), wall=(624, 666), panes=2),
]

SPAWNS = {
    'living':  (600, 585, 0.62),
    'kitchen': (725, 432, -2.85),
    'bedroom': (200, 250, 2.65),
    'study':   (1110, 585, 0.80),
    'closet':  (135, 210, 0.0),                   # from the bedroom, looking through the arch into the closet
    'hall':    (731, 45, 3.1416),
    'bath':    (918, 62, -2.25),
    'wc':      (515, 53, 1.5708),
}

OUTDOOR = ()


def room_area(key):
    return sum((r[2] - r[0]) * (r[3] - r[1]) for r in ROOMS[key]['rects']) * S * S


def net_area():
    return sum(room_area(k) for k in ROOMS if k not in OUTDOOR)


# ---------------------------------------------------------------- flat specific build settings
ID = 'garden'
META = dict(
    title='Garden flat',
    eyebrow='Ground floor · 3 rooms',
    lede='Three rooms on the raised ground floor of an older building, with tall windows facing the garden.',
    stats=[['66.2', 'm²', 'Interior, from the plan'], ['2.95', 'm', 'Ceiling height, approx.'],
           ['19.1', 'm²', 'Living room'], ['3', '', 'Rooms + kitchen']],
    note='Room sizes come from the architect\'s plan, which is dimensioned in centimetres.',
)
BOUNDS_PX = (-65, -25, 1248, 666)
EXTRA_COLLIDERS_PX = []
SILL_TILE_ROOMS = ()
SKIRTING = [('living', 'wood_beech', 0.06), ('bedroom', 'wood_beech', 0.06), ('study', 'wood_beech', 0.06),
            ('hall', 'wood_beech', 0.06), ('closet', 'wood_beech', 0.06), ('kitchen', 'wood_beech', 0.06)]
CLADDING = [('bath', 1.55, 'tile_beige', {}), ('wc', 1.20, 'tile_beige', {})]
MAT_ALIASES = {'door_frame': 'frame_grey', 'door_leaf': 'wood_beech', 'door_entry': 'wood_beech'}
FILLS = {
    'living': [(462, 388, 3.2, 3.8, 22)],
    'kitchen': [(770, 500, 1.4, 2.0, 22)],
    'bedroom': [(125, 388, 1.8, 3.8, 14)],
    'study': [(1042, 433, 2.6, 3.0, 16)],
    'closet': [(140, 53, 2.2, 0.8, 8)],
    'hall': [(706, 53, 2.8, 0.8, 16), (770, 238, 1.5, 2.2, 18)],
    'bath': [(970, 116, 1.5, 1.9, 22)],
    'wc': [(431, 53, 1.6, 0.8, 10)],
}
SUN = dict(elevation=30, azimuth=158, energy=45.0)   # from the south-south-east, into the garden windows
VIEW_ROTATION = 4.7124                              # the panorama is centred on the garden (south)
OUTSIDE_PROBE = 'living'                              # viewer: light the facade like the living room (neutral)
VIEWS = {
    'living_wall': (400, 560, 0.0, 1.55, -0.05),     # looking north at the shelving wall
    'living_sofa': (600, 330, 2.05, 1.55, -0.08),    # from the hall door towards the sofa and clock
    'living_garden': (330, 260, -2.55, 1.55, -0.05), # towards the kitchen and the garden door
    'bedroom_b': (60, 560, -0.35, 1.50, -0.05),
    'study_b': (1150, 600, 0.75, 1.50, -0.05),
    'kitchen_b': (800, 600, 0.6, 1.50, -0.15),
    'hall_b': (770, 330, 0.0, 1.55, -0.05),
}


# ---------------------------------------------------------------- furniture
def furnish(b):
    """Place the furniture seen in the photos. `b` is the build module namespace."""
    globals().update({k: v for k, v in vars(b).items() if not k.startswith('__')})
    import furniture2 as F2

    # ---------------- living room 4.05 x 4.72, windows south, shelving wall north
    L = 'living'
    place(F2.wall_unit(3.70, 2.50, 0.36), 'wall_unit', L, 2.025, 0.18, 'S', solid=True)
    place(F2.sofa_corner(2.70, 0.95, 1.62), 'sofa', L, 0.475, 2.70, 'E', solid=True)
    place(F2.wall_clock(0.72), 'wall_clock', L, 0.004, 2.72, 'E', z=1.88)
    place(F2.dining_table_white(1.30, 0.80), 'dining_table', L, 2.55, 1.45, 'S', solid=True)
    for i, (u, v, f) in enumerate(((2.25, 0.86, 'S'), (2.85, 0.86, 'S'), (2.25, 2.06, 'N'), (2.85, 2.06, 'N'))):
        place(F2.conf_chair(), f'chair_{i}', L, u, v, f)
    place(F2.chandelier(0.42, 0.55), 'chandelier', L, 2.0, 2.45, z=H)
    ob = place(F2.runner(0.62, 2.60), 'runner_hall_side', L, 3.65, 2.00, 'S')
    ob = place(F2.runner(1.25, 0.55), 'runner_garden', L, 3.40, 4.38, 'S')
    place(F2.runner(0.95, 0.55, 'rug_white'), 'rug_sofa', L, 1.62, 2.60, 'E')
    place(F.radiator(1.0), 'radiator_living', L, 1.03, 4.65, 'N', z=0.12)
    place(F.curtain_rod(1.55), 'rod_living_win', L, 1.03, 4.61, 'N', z=2.86)
    place(F.curtain(0.55, 2.80), 'curtain_living_l', L, 0.40, 4.60, 'N', z=0.04)
    place(F.curtain(0.55, 2.80), 'curtain_living_r', L, 1.66, 4.60, 'N', z=0.04)
    place(F.curtain_rod(1.45), 'rod_living_door', L, 3.39, 4.61, 'N', z=2.86)
    place(F.curtain(0.60, 2.80), 'curtain_garden_l', L, 2.85, 4.60, 'N', z=0.04)
    place(F2.picture(0.30, 0.40, 'art_lemons'), 'print_lemons', L, 0.012, 1.60, 'E', z=1.35)
    place(F2.picture(0.34, 0.22, 'art_arch', 'white_matt'), 'sign_home', L, 0.012, 0.98, 'E', z=2.18)
    place(F2.picture(0.30, 0.40, 'art_lemons_blue'), 'print_lemons_blue', L, 4.038, 2.05, 'W', z=1.40)
    for nm in ('print_lemons', 'sign_home', 'print_lemons_blue'):
        fit_uv(bpy.data.objects[nm], 'xz')
    x, y = R(L, 0.30, 4.40)
    place(F.pot(0.18, 0.32, 'terracotta'), 'pot_dracaena', L, 0.30, 4.40)
    import_model('pachira_aquatica_01', 'plant_dracaena', L, (x, y, 0.29), rz=1.1, height=1.55, keep=['_c'])
    for i, u in enumerate((0.70, 1.30)):
        x, y = R(L, u, 4.80)
        import_model('potted_plant_04', f'plant_sill_{i}', L, (x, y, 0.86), rz=i, height=0.24, drop=['ground'])
    x, y = R(L, 2.10, 0.20)
    import_model('potted_plant_02', 'plant_shelf', L, (x, y, 1.222), rz=0.4, height=0.45)

    # ---------------- bedroom 2.50 x 4.72 (mattress, macrame, dreamcatcher)
    Bd = 'bedroom'
    place(F2.mattress_floor(1.40, 2.00), 'mattress', Bd, 0.71, 3.66, 'N', solid=True)
    place(F2.canvas(0.90, 0.60, 'canvas_dream'), 'canvas_dream', Bd, 0.017, 3.55, 'E', z=1.05)
    fit_uv(bpy.data.objects['canvas_dream'], 'xz')
    place(F.curtain_rod(1.40), 'rod_bedroom', Bd, 1.60, 4.61, 'N', z=2.86)
    place(F.curtain(1.25, 2.80, folds=9, amp=0.025), 'curtain_bedroom', Bd, 1.60, 4.62, 'N', z=0.04)
    place(F2.macrame(0.80, 1.75), 'macrame', Bd, 1.60, 4.56, 'N', z=2.80)
    place(F.lantern(0.70), 'lantern_bedroom', Bd, 1.25, 2.40, z=H)
    place(F2.string_lights(1.60), 'string_lights', Bd, 2.49, 3.10, 'W', z=2.05)
    place(F.radiator(1.0), 'radiator_bedroom', Bd, 1.60, 4.65, 'N', z=0.12)
    x, y = R(Bd, 2.05, 4.30)
    place(F.pot(0.17, 0.28, 'terracotta'), 'pot_monstera', Bd, 2.05, 4.30)
    import_model('calathea_orbifolia_01', 'plant_monstera', Bd, (x, y, 0.25), rz=0.5, height=0.85, keep=['_b'])
    place(F2.runner(0.80, 1.20, 'rug_white'), 'rug_bedroom', Bd, 1.80, 3.20, 'S')

    # ---------------- walk-in closet 2.80 x 1.07 (pine loft frame)
    place(F2.loft_frame(2.66, 1.00, 2.05), 'loft_frame', 'closet', 1.40, 0.535, 'S', solid=True)

    # ---------------- study 3.32 x 3.82 (sofa bed, two desks, wardrobe)
    St = 'study'
    place(F2.sofa_bed_small(1.45, 0.88), 'sofa_bed', St, 2.88, 2.60, 'W', solid=True)
    place(F2.desk_simple(1.00, 0.50, 'white_matt', 'metal_black'), 'desk_window', St, 0.60, 3.57, 'N', solid=True)
    place(F2.folding_chair_wood(), 'chair_folding', St, 0.62, 3.05, 'S')
    place(F2.desk_dark(1.00, 0.50), 'desk_dark', St, 0.82, 0.25, 'S', solid=True)
    place(F2.chair_white(), 'chair_white', St, 0.80, 0.78, 'N')
    place(F.drawers(0.40, 0.40, 0.62, 3), 'drawers_pine', St, 1.55, 0.21, 'S', solid=True)
    place(F2.wardrobe(0.75, 0.55, 1.90), 'wardrobe', St, 2.20, 0.29, 'S', solid=True)
    x, y = R(St, 2.92, 0.30)
    place(F.pot(0.15, 0.26, 'ceramic_white'), 'pot_study', St, 2.92, 0.30)
    import_model('pachira_aquatica_01', 'plant_study', St, (x, y, 0.23), rz=2.2, height=1.20, keep=['_d'])
    place(F.lantern(0.62), 'lantern_study', St, 1.66, 1.90, z=H)
    place(F.radiator(1.0), 'radiator_study', St, 1.42, 3.75, 'N', z=0.12)
    place(F.curtain_rod(1.50), 'rod_study', St, 1.42, 3.71, 'N', z=2.86)
    place(F.curtain(0.55, 2.80), 'curtain_study_l', St, 0.80, 3.70, 'N', z=0.04)
    place(F.curtain(0.55, 2.80), 'curtain_study_r', St, 2.04, 3.70, 'N', z=0.04)
    place(F2.runner(0.70, 1.10, 'rug_white'), 'rug_study', St, 2.15, 2.60, 'W')

    # ---------------- kitchen 1.91 x 2.45 (run along the east wall, window south)
    K = 'kitchen'
    place(F2.tall_oven(0.60, 0.60, 2.10), 'tall_oven', K, 1.61, 0.30, 'W', solid=True)
    place(F2.base_run(1.85, sink_at=-0.20, hob_at=0.55), 'kitchen_run', K, 1.61, 1.525, 'W', solid=True)
    place(F2.uppers(1.85, 0.72, 0.34), 'kitchen_uppers', K, 1.74, 1.525, 'W', z=1.52)
    place(F2.splashback(1.85, 0.62), 'splashback', K, 1.906, 1.525, 'W', z=0.90)
    g = Geo()
    g.add(box(0.46, 0.34, 0.26, bevel=0.01), M['appliance_white'])
    g.add(box(0.30, 0.006, 0.20, at=(-0.06, -0.172, 0.03)), M['screen'])
    g.add(lathe([(0.0, 0.0), (0.075, 0.0), (0.085, 0.03), (0.08, 0.17), (0.055, 0.22), (0.0, 0.225)], seg=28),
          M['fab_olive'], loc=(0.40, 0.0, 0.0))
    place(g, 'microwave_kettle', K, 1.66, 0.78, 'W', z=0.90)
    place(F2.bell_pendant(0.85), 'pendant_kitchen', K, 0.95, 1.20, z=H)
    place(F2.dish_rack(), 'dish_rack', K, 0.54, 2.22, 'N', solid=True)
    place(F2.picture(0.30, 0.42, 'art_arch'), 'print_kitchen', K, 0.012, 1.80, 'E', z=1.35)
    fit_uv(bpy.data.objects['print_kitchen'], 'xz')
    place(F.curtain_rod(0.80), 'rod_kitchen', K, 0.54, 2.40, 'N', z=1.85)
    place(F.curtain(0.70, 0.90, folds=5, amp=0.02), 'curtain_kitchen', K, 0.54, 2.41, 'N', z=0.95)
    x, y = R(K, 0.54, 2.62)
    import_model('potted_plant_04', 'plant_kitchen', K, (x, y, 0.91), height=0.22, drop=['ground'])

    # ---------------- bathroom 1.87 x 2.32 (tub along the east wall, basin and washer on the south wall)
    Bt = 'bath'
    place(F.bathtub(1.70, 0.75, 0.55), 'bathtub', Bt, 1.495, 0.95, rz=pi / 2, solid=True)
    place(F2.glass_screen(0.80, 1.40), 'glass_screen', Bt, 1.115, 0.52, 'E', z=0.56)
    place(F.shower_mixer(), 'shower_mixer', Bt, 1.87, 0.55, 'W', z=0.80)
    place(F2.basin_wall(0.60, 0.45), 'basin', Bt, 0.95, 2.095, 'N', z=0.70, solid=True)
    place(F2.mirror_cabinet(0.70, 0.62, 0.14), 'mirror_cabinet', Bt, 0.95, 2.25, 'N', z=1.25)
    g = Geo()
    g.add(box(0.72, 0.006, 0.22, bevel=0.0), M['mosaic'])
    place(g, 'mosaic', Bt, 0.95, 2.315, 'N', z=1.00)
    place(F2.washer(0.60, 0.58, 0.85), 'washer', Bt, 0.31, 2.03, 'N', solid=True)
    place(F2.boiler(0.22, 0.80), 'boiler', Bt, 0.31, 2.09, 'N', z=1.45)
    place(F2.plywood_cabinet(0.60, 0.40, 0.90), 'cabinet_plywood', Bt, 0.55, 0.20, 'S', solid=True)
    x, y = R(Bt, 0.55, 0.20)
    import_model('potted_plant_02', 'plant_bath', Bt, (x, y, 0.90), rz=1.0, height=0.48)
    place(F.flush_light(0.16), 'light_bath', Bt, 0.93, 1.16, z=H)

    # ---------------- WC 2.05 x 1.07 (wall-hung pan on the installation wall)
    Wc = 'wc'
    place(F2.prewall(1.07, 1.15, 0.20), 'wc_prewall', Wc, 0.0, 0.535, 'E', solid=True)
    place(F2.toilet_wallhung(), 'toilet', Wc, 0.20, 0.535, 'E', solid=True)
    place(F.wall_shelf(0.45, 0.15), 'wc_shelf', Wc, 0.85, 0.08, 'S', z=1.05)
    place(F.paper_stand(), 'paper_stand', Wc, 0.50, 0.95, 'N')
    place(F2.picture(0.32, 0.42, 'art_arch', 'wood_oak'), 'print_wc', Wc, 0.207, 0.535, 'E', z=1.45)
    fit_uv(bpy.data.objects['print_wc'], 'xz')
    place(F.flush_light(0.13), 'light_wc', Wc, 1.02, 0.53, z=H)

    # ---------------- hall: entrance corridor (rect 0) and inner hall (rect 1)
    Hl = 'hall'
    place(F.curtain_rod(0.80), 'rod_niche', Hl, 2.80, 0.58, 'S', z=2.32, i=0)
    place(F.curtain(0.78, 2.26, folds=8, amp=0.03, matname='curtain_cream'), 'curtain_niche', Hl, 2.80, 0.58, 'S', z=0.05, i=0)
    place(F2.skirt_cabinet(1.00, 0.42, 0.85), 'hall_cabinet', Hl, 1.70, 0.73, 'W', solid=True, i=1)
    place(F2.step_shelf(0.36, 0.36), 'step_shelf', Hl, 0.80, 2.44, 'N', solid=True, i=1)
    place(F2.canvas(0.24, 0.62, 'sign_ocean'), 'sign_ocean', Hl, 0.55, 2.605, 'N', z=1.30, i=1)
    fit_uv(bpy.data.objects['sign_ocean'], 'xz')
    place(F2.round_mirror(0.17), 'round_mirror', Hl, 1.35, 2.61, 'N', z=1.85, i=1)
    g = Geo()
    g.add(box(0.75, 0.48, 0.012, bevel=0.003), M['coir'])
    place(g, 'door_mat', Hl, 1.85, 0.32, 'S', i=0)
    place(F.flush_light(0.15), 'light_hall_a', Hl, 1.60, 0.53, z=H, i=0)
    place(F.flush_light(0.15), 'light_hall_b', Hl, 0.95, 1.30, z=H, i=1)
