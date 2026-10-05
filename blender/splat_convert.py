"""Turn a trained Gaussian splat (OpenSplat / 3DGS .ply in COLMAP coordinates) into a web-sized .splat file
standing upright in metres, plus the photo cameras for the viewer.
   python3 blender/splat_convert.py <splat.ply> <cameras.json> <out dir> [--ceiling 2.95] [--eye 1.45] [--radius 9] [--max 600000]

COLMAP's frame has an arbitrary orientation and scale. "Up" is taken from the photos (people hold phones level),
the floor is the lowest dense layer of splats, and the scale comes from the known ceiling height (--ceiling: floor to
the highest dense layer) or, failing that, assumes the photos were taken at --eye metres on average.
Writes .splat (32 bytes a splat: position, scale, RGBA, rotation) and .spz (compressed); both drop the view-dependent
colour terms (the splat is trained without them)."""
import gzip
import json
import os
import sys

import numpy as np

args = sys.argv[1:]
src, cams_path, out = args[0], args[1], args[2]
opt = {k: float(args[args.index(k) + 1]) for k in ('--eye', '--radius', '--max', '--ceiling') if k in args}
EYE, RADIUS, MAXN = opt.get('--eye', 1.45), opt.get('--radius', 9.0), int(opt.get('--max', 600000))
os.makedirs(out, exist_ok=True)
SH_C0 = 0.28209479177387814


def read_ply(path):
    with open(path, 'rb') as f:
        names, n = [], 0
        while True:
            line = f.readline().decode().strip()
            if line.startswith('element vertex'):
                n = int(line.split()[-1])
            elif line.startswith('property'):
                names.append(line.split()[-1])
            elif line == 'end_header':
                break
        data = np.frombuffer(f.read(n * 4 * len(names)), dtype=np.float32).reshape(n, len(names))
    return {k: data[:, i] for i, k in enumerate(names)}


def quat_to_mat(q):            # q: (n, 4) w, x, y, z
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
                     2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
                     2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1).reshape(-1, 3, 3)


def mat_to_quat(m):            # m: (n, 3, 3) -> (n, 4) w, x, y, z
    t = m[:, 0, 0] + m[:, 1, 1] + m[:, 2, 2]
    q = np.zeros((len(m), 4))
    q[:, 0] = np.sqrt(np.maximum(0, 1 + t)) / 2
    q[:, 1] = np.sqrt(np.maximum(0, 1 + m[:, 0, 0] - m[:, 1, 1] - m[:, 2, 2])) / 2 * np.sign(m[:, 2, 1] - m[:, 1, 2])
    q[:, 2] = np.sqrt(np.maximum(0, 1 - m[:, 0, 0] + m[:, 1, 1] - m[:, 2, 2])) / 2 * np.sign(m[:, 0, 2] - m[:, 2, 0])
    q[:, 3] = np.sqrt(np.maximum(0, 1 - m[:, 0, 0] - m[:, 1, 1] + m[:, 2, 2])) / 2 * np.sign(m[:, 1, 0] - m[:, 0, 1])
    return q / np.linalg.norm(q, axis=1, keepdims=True)


g = read_ply(src)
cams = json.load(open(cams_path))
pos = np.stack([g['x'], g['y'], g['z']], 1).astype(np.float64)
alpha = 1 / (1 + np.exp(-g['opacity']))

# up: photos are tilted up and down but rarely rolled, so their sideways axes are level; up is the direction
# most perpendicular to all of them (OpenSplat writes OpenCV cameras: columns of camera-to-world are right, down, forward)
C = np.array([c['position'] for c in cams])
Rc = np.array([c['rotation'] for c in cams])
rights = Rc[:, :, 0]
up = np.linalg.eigh(rights.T @ rights)[1][:, 0]
if up @ Rc[:, :, 1].mean(0) > 0:
    up = -up
# horizontal axes: the mean viewing direction becomes -Z (the viewer opens looking the way most photos look)
fwd = Rc[:, :, 2].mean(0)
fwd -= up * fwd.dot(up)
fwd /= np.linalg.norm(fwd)
right = np.cross(fwd, up)
A = np.stack([right, up, -fwd])          # rows: new x, y, z in old coordinates

# floor: low percentile of the heights of solid splats near the cameras; scale from the photo height
h = pos @ up
near = np.linalg.norm((pos - C.mean(0)) - np.outer(h - C.mean(0) @ up, up), axis=1)
solid = alpha >= min(0.5, np.percentile(alpha, 70))     # >=: right after an opacity reset every splat is equally faint
core = solid & (near < np.percentile(near[solid], 60))
floor, ceil = np.percentile(h[core], 1.5), np.percentile(h[core], 98.5)
cam_h = C @ up - floor
s = EYE / cam_h.mean()
if '--ceiling' in opt:
    print(f'scale from the photo height {s:.3f}, from the ceiling {opt["--ceiling"] / (ceil - floor):.3f}')
    s = opt['--ceiling'] / (ceil - floor)
origin = C.mean(0) - up * (C.mean(0) @ up - floor)
print(f'{len(pos)} splats; camera heights {np.round(cam_h * s, 2)} m; scale {s:.3f}')

P = (pos - origin) @ A.T * s
keep = (np.linalg.norm(P - P.mean(0), axis=1) < RADIUS) & (alpha > 0.02) & (P[:, 1] > -0.3)
quat = np.stack([g['rot_0'], g['rot_1'], g['rot_2'], g['rot_3']], 1).astype(np.float64)
quat /= np.linalg.norm(quat, axis=1, keepdims=True)
Q = mat_to_quat(A[None] @ quat_to_mat(quat))
logs = np.stack([g['scale_0'], g['scale_1'], g['scale_2']], 1) + np.log(s)
rgb = np.clip(0.5 + SH_C0 * np.stack([g['f_dc_0'], g['f_dc_1'], g['f_dc_2']], 1), 0, 1)

idx = np.where(keep)[0]
importance = np.exp(logs[idx].sum(1)) * alpha[idx]
idx = idx[np.argsort(-importance)][:MAXN]
rec = np.zeros(len(idx), dtype=[('p', '<f4', 3), ('s', '<f4', 3), ('c', 'u1', 4), ('r', 'u1', 4)])
rec['p'] = P[idx]
rec['s'] = np.exp(logs[idx])
rec['c'][:, :3] = np.round(rgb[idx] * 255)
rec['c'][:, 3] = np.round(alpha[idx] * 255)
rec['r'] = np.clip(np.round(Q[idx] * 128 + 128), 0, 255)
rec.tofile(os.path.join(out, 'living.splat'))

# the same splats as .spz (Niantic's format, version 2: gzip of fixed-point positions and 8-bit attributes), about a
# third of the size; the viewer loads this one
n = len(idx)
fixed = np.round(P[idx] * 4096).astype(np.int32)                       # 12 fractional bits
pos24 = np.stack([fixed & 0xff, (fixed >> 8) & 0xff, (fixed >> 16) & 0xff], -1).astype(np.uint8)
dc = np.stack([g['f_dc_0'], g['f_dc_1'], g['f_dc_2']], 1)[idx]
q = Q[idx][:, [1, 2, 3, 0]] * np.where(Q[idx][:, :1] < 0, -1, 1)        # x, y, z with w >= 0 implied
u8 = lambda v: np.clip(np.round(v), 0, 255).astype(np.uint8)
body = b''.join([np.array([0x5053474e, 2, n], '<u4').tobytes(), bytes([0, 12, 0, 0]),
                 pos24.tobytes(), u8(alpha[idx] * 255).tobytes(), u8(dc * 0.15 * 255 + 127.5).tobytes(),
                 u8((logs[idx] + 10) * 16).tobytes(), u8(q[:, :3] * 127.5 + 127.5).tobytes()])
with gzip.open(os.path.join(out, 'living.spz'), 'wb', compresslevel=9) as f:
    f.write(body)

# cameras for the viewer: position and a three.js quaternion (x, y, z, w), vertical field of view
views = []
for c in cams:
    R = A @ np.array(c['rotation']) @ np.diag([1.0, -1.0, -1.0])     # OpenCV camera -> three.js camera (looks down -Z)
    w, x, y, z = mat_to_quat(R[None])[0]
    views.append(dict(name=c['img_name'], position=list(np.round((np.array(c['position']) - origin) @ A.T * s, 4)),
                      quaternion=[round(v, 6) for v in (x, y, z, w)],
                      fov=round(float(np.degrees(2 * np.arctan(c['height'] / (2 * c['fy'])))), 3),
                      aspect=round(c['width'] / c['height'], 4)))
views.sort(key=lambda v: v['name'])
json.dump(dict(splats=len(idx), scale=round(s, 4), views=views), open(os.path.join(out, 'views.json'), 'w'), indent=1)
size = lambda f: os.path.getsize(os.path.join(out, f)) / 1e6
print(f'wrote {len(idx)} splats ({size("living.splat"):.1f} MB .splat, {size("living.spz"):.1f} MB .spz) and {len(views)} views to {out}')
