// Gaussian splat test of the garden flat's living room (splat.html).
// The splat and the photo cameras come from blender/splat_convert.py: metres, Y up, floor at y = 0.
// The frame is 4:3 like the photos, so at a photo viewpoint the splat and the photo line up exactly.
import * as THREE from 'three';
import { SparkRenderer, SplatMesh, SplatFileType } from '@sparkjsdev/spark';

const BASE = 'assets/garden/splat/';
// photo file name -> label, in the order the list shows them
const LABELS = {
  '20260910_104843': 'Sofa, straight on',
  '20260910_104610': 'Sofa and window',
  '20260910_105201': 'Clock wall',
  '20260910_104627': 'Sofa to the shelves',
  '20260910_104630': 'Shelving wall',
  '20260910_104852': 'Dining table',
  '20260910_104855': 'Table and shelves',
  '20260910_105258': 'From the far corner',
};
const SPEED = 1.1, FAST = 2.4;          // m/s
const $ = (id) => document.getElementById(id);
const frame = $('frame'), hint = $('hint');
if (matchMedia('(pointer: coarse)').matches) hint.textContent = 'Drag to look · pinch to move';

const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.setClearColor(getComputedStyle(frame).backgroundColor);
frame.prepend(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, 4 / 3, 0.05, 60);
camera.rotation.order = 'YXZ';
scene.add(new SparkRenderer({ renderer }));

const S = {
  views: [], at: -1, tween: null, keys: new Set(), center: new THREE.Vector3(), radius: 4,
  yaw: 0, pitch: 0, roll: 0, compare: false, split: 50, moved: false,
};

function resize() {
  const w = frame.clientWidth, h = frame.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(frame);

// ---------- loading (fetch ourselves for a progress bar, then hand the bytes to Spark)
async function fetchBytes(url, onProgress) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const total = +res.headers.get('content-length') || 0;
  if (!res.body) return new Uint8Array(await res.arrayBuffer());
  const reader = res.body.getReader(), chunks = [];
  let got = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    got += value.length;
    if (total) onProgress(Math.min(1, got / total));
  }
  const out = new Uint8Array(got);
  let o = 0;
  for (const c of chunks) { out.set(c, o); o += c.length; }
  return out;
}

async function load() {
  const info = await (await fetch(BASE + 'views.json')).json();
  const bytes = await fetchBytes(BASE + 'living.spz', (p) => { $('loadBar').style.width = `${Math.round(p * 100)}%`; });
  $('loadText').textContent = 'Preparing…';
  const mesh = new SplatMesh({ fileBytes: bytes, fileType: SplatFileType.SPZ });
  scene.add(mesh);
  S.mesh = mesh;
  await mesh.initialized;

  const order = Object.keys(LABELS);
  S.views = info.views
    .map((v) => ({ ...v, id: v.name.replace(/\.jpg$/i, '') }))
    .filter((v) => LABELS[v.id])
    .sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id))
    .map((v) => ({ ...v, label: LABELS[v.id], pos: new THREE.Vector3(...v.position), quat: new THREE.Quaternion(...v.quaternion) }));
  for (const v of S.views) S.center.add(v.pos);
  S.center.divideScalar(S.views.length);
  S.radius = Math.max(...S.views.map((v) => Math.hypot(v.pos.x - S.center.x, v.pos.z - S.center.z))) + 1.5;

  const list = $('views');
  S.views.forEach((v, i) => {
    const li = document.createElement('li');
    li.innerHTML = `<button type="button"><span>${i + 1}</span>${v.label}</button>`;
    li.firstChild.addEventListener('click', () => goView(i));
    list.append(li);
  });
  $('statSplats').textContent = info.splats.toLocaleString('en-US');
  $('stats').hidden = false;

  const start = Math.max(0, Math.min(S.views.length - 1, (parseInt(location.hash.slice(1), 10) || 1) - 1));
  goView(start, true);
  $('loading').hidden = true;
}

// ---------- camera: a photo viewpoint, a tween between viewpoints, or free look and move
function setLook(q) {
  const e = new THREE.Euler().setFromQuaternion(q, 'YXZ');
  S.pitch = e.x; S.yaw = e.y; S.roll = e.z;
}
function applyLook() {
  camera.rotation.set(S.pitch, S.yaw, S.roll, 'YXZ');
}

function goView(i, instant = false) {
  const v = S.views[i];
  const from = { pos: camera.position.clone(), quat: camera.quaternion.clone(), fov: camera.fov };
  const dist = from.pos.distanceTo(v.pos) + 2 * from.quat.angleTo(v.quat);
  S.tween = instant ? null : { from, to: v, t: 0, dur: Math.min(1.8, 0.6 + dist * 0.35) };
  if (instant) arrive(v);
  S.at = -1;
  markView(i);
  setCompareVisible();
  history.replaceState(null, '', `#${i + 1}`);
}
function arrive(v) {
  camera.position.copy(v.pos);
  camera.quaternion.copy(v.quat);
  camera.fov = v.fov;
  camera.updateProjectionMatrix();
  setLook(v.quat);
  S.at = S.views.indexOf(v);
  S.tween = null;
  $('photoImg').src = `${BASE}photos/${v.id}.jpg`;
  setCompareVisible();
}
function markView(i) {
  [...$('views').querySelectorAll('button')].forEach((b, j) => b.setAttribute('aria-current', String(j === i)));
}
function leaveView() {
  if (S.tween) { setLook(camera.quaternion); S.tween = null; }
  if (S.at < 0) return;
  S.at = -1;
  markView(-1);
  setCompareVisible();
  history.replaceState(null, '', location.pathname + location.search);
}

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
function stepTween(dt) {
  const tw = S.tween;
  tw.t = Math.min(1, tw.t + dt / tw.dur);
  const e = ease(tw.t);
  camera.position.lerpVectors(tw.from.pos, tw.to.pos, e);
  camera.quaternion.slerpQuaternions(tw.from.quat, tw.to.quat, e);
  camera.fov = THREE.MathUtils.lerp(tw.from.fov, tw.to.fov, e);
  camera.updateProjectionMatrix();
  if (tw.t >= 1) arrive(tw.to);
}

const fwd = new THREE.Vector3(), side = new THREE.Vector3(), move = new THREE.Vector3();
function moveBy(dx, dy, dz) {            // metres: dx right, dy up, dz forward (along the view, flattened)
  leaveView();
  fwd.set(-Math.sin(S.yaw), 0, -Math.cos(S.yaw));
  side.set(Math.cos(S.yaw), 0, -Math.sin(S.yaw));
  move.copy(fwd).multiplyScalar(dz).addScaledVector(side, dx);
  move.y = dy;
  camera.position.add(move);
  // stay in the room: a disc around the photo positions, between the floor and the ceiling
  const off = camera.position.clone().sub(S.center);
  off.y = 0;
  if (off.length() > S.radius) camera.position.sub(off.multiplyScalar(1 - S.radius / off.length()));
  camera.position.y = THREE.MathUtils.clamp(camera.position.y, 0.35, 2.6);
  nudgeHint();
}
function dolly(d) {                       // along the actual view direction (into the picture)
  leaveView();
  camera.getWorldDirection(move);
  camera.position.addScaledVector(move, d);
  moveBy(0, 0, 0);
}

function nudgeHint() {
  if (S.moved) return;
  S.moved = true;
  hint.style.opacity = 0;
}

// ---------- input
const ptrs = new Map();
let pinch = 0;
frame.addEventListener('pointerdown', (e) => {
  if (e.target === $('divider')) return;
  frame.setPointerCapture(e.pointerId);
  ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (ptrs.size === 2) pinch = pinchDist();
  frame.classList.add('dragging');
});
frame.addEventListener('pointermove', (e) => {
  const p = ptrs.get(e.pointerId);
  if (!p) return;
  const dx = e.clientX - p.x, dy = e.clientY - p.y;
  p.x = e.clientX; p.y = e.clientY;
  if (ptrs.size === 2) {
    const d = pinchDist();
    dolly((d - pinch) * 0.008);
    pinch = d;
    return;
  }
  if (!dx && !dy) return;
  leaveView();
  // grab the picture: it follows the pointer
  const k = THREE.MathUtils.degToRad(camera.fov) / frame.clientHeight;
  S.yaw += dx * k;
  S.pitch = THREE.MathUtils.clamp(S.pitch + dy * k, -1.35, 1.35);
  S.roll *= 0.9;
  applyLook();
  nudgeHint();
});
const endPtr = (e) => {
  ptrs.delete(e.pointerId);
  if (!ptrs.size) frame.classList.remove('dragging');
};
frame.addEventListener('pointerup', endPtr);
frame.addEventListener('pointercancel', endPtr);
function pinchDist() {
  const [a, b] = [...ptrs.values()];
  return Math.hypot(a.x - b.x, a.y - b.y);
}
frame.addEventListener('wheel', (e) => {
  e.preventDefault();
  dolly(THREE.MathUtils.clamp(-e.deltaY * (e.deltaMode ? 0.05 : 0.0018), -0.5, 0.5));
}, { passive: false });

const MOVE_KEYS = ['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyQ', 'KeyE', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ShiftLeft', 'ShiftRight'];
addEventListener('keydown', (e) => {
  if (e.target.closest?.('input, [role="slider"]') && e.code.startsWith('Arrow')) return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const n = /^Digit([1-9])$/.exec(e.code);
  if (n && +n[1] <= S.views.length) { goView(+n[1] - 1); return; }
  if (MOVE_KEYS.includes(e.code)) { S.keys.add(e.code); e.preventDefault(); }
});
addEventListener('keyup', (e) => S.keys.delete(e.code));
addEventListener('blur', () => S.keys.clear());

function keyMove(dt) {
  const k = S.keys;
  if (!k.size) return;
  const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
  const r = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
  const u = (k.has('KeyE') ? 1 : 0) - (k.has('KeyQ') ? 1 : 0);
  if (!f && !r && !u) return;
  const v = (k.has('ShiftLeft') || k.has('ShiftRight') ? FAST : SPEED) * dt;
  const n = Math.hypot(f, r) || 1;
  moveBy(r / n * v, u * v * 0.7, f / n * v);
}

// ---------- compare with the photo (only meaningful exactly at a viewpoint)
const divider = $('divider'), photo = $('photo');
function setSplit(p) {
  S.split = THREE.MathUtils.clamp(p, 0, 100);
  divider.style.left = `${S.split}%`;
  photo.style.clipPath = `inset(0 0 0 ${S.split}%)`;
  divider.setAttribute('aria-valuenow', String(Math.round(S.split)));
}
function setCompareVisible() {
  frame.classList.toggle('compare', S.compare && S.at >= 0);
  if (S.compare && S.at < 0 && S.moved) {
    hint.textContent = 'Pick a photo viewpoint to compare';
    hint.style.opacity = 1;
  } else if (S.moved) {
    hint.style.opacity = 0;
  }
}
$('compare').addEventListener('change', (e) => {
  S.compare = e.target.checked;
  if (S.compare && !S.preloaded) {
    S.preloaded = S.views.map((v) => Object.assign(new Image(), { src: `${BASE}photos/${v.id}.jpg` }));
  }
  if (S.compare && S.at < 0 && !S.tween) {
    // snap back to the nearest viewpoint
    let best = 0, bd = Infinity;
    S.views.forEach((v, i) => {
      const d = v.pos.distanceTo(camera.position) + v.quat.angleTo(camera.quaternion);
      if (d < bd) { bd = d; best = i; }
    });
    goView(best);
  }
  setCompareVisible();
});
divider.addEventListener('pointerdown', (e) => {
  e.stopPropagation();
  divider.setPointerCapture(e.pointerId);
  const r = frame.getBoundingClientRect();
  const mv = (ev) => setSplit((ev.clientX - r.left) / r.width * 100);
  const up = () => { divider.removeEventListener('pointermove', mv); divider.removeEventListener('pointerup', up); };
  divider.addEventListener('pointermove', mv);
  divider.addEventListener('pointerup', up);
});
divider.addEventListener('keydown', (e) => {
  const d = { ArrowLeft: -5, ArrowRight: 5 }[e.code];
  if (d) { setSplit(S.split + d); e.preventDefault(); }
});
setSplit(50);

// ---------- loop
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (S.tween) stepTween(dt);
  keyMove(dt);
  renderer.render(scene, camera);
});

resize();
load().catch((err) => {
  console.error(err);
  $('loading').classList.add('error');
  $('loadText').textContent = `Could not load the splat (${err.message}).`;
});
window.splat = { S, scene, camera, renderer, goView, moveBy };
