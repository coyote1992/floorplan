import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

/* ------------------------------------------------------------------ tuning */
const EYE = 1.6;               // eye height in walk mode (m)
const RADIUS = 0.22;           // body radius for collisions (m)
const LM_GAIN = 1.0;           // lightmap brightness multiplier
const EMISSIVE_GAIN = 0.35;    // lamp shades / bulbs
const EXPOSURE = 1.0;

const $ = id => document.getElementById(id);
const canvas = $('view');
const stage = $('stage');
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ------------------------------------------------------------------ renderer, cameras, controls */
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NeutralToneMapping;
renderer.toneMappingExposure = EXPOSURE;

const scene = new THREE.Scene();
const camWalk = new THREE.PerspectiveCamera(72, 1, 0.03, 5000);
camWalk.rotation.order = 'YXZ';
const camOrbit = new THREE.PerspectiveCamera(38, 1, 0.1, 5000);
const camPlan = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
let camera = camOrbit;

const orbit = new OrbitControls(camOrbit, canvas);
orbit.enableDamping = true;
orbit.dampingFactor = 0.08;
orbit.minDistance = 3;
orbit.maxDistance = 45;
orbit.maxPolarAngle = 1.32;
const planCtl = new OrbitControls(camPlan, canvas);
planCtl.enableRotate = false;
planCtl.screenSpacePanning = true;
planCtl.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };
planCtl.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_PAN };
planCtl.minZoom = 0.6;
planCtl.maxZoom = 6;
planCtl.enabled = false;

/* ------------------------------------------------------------------ state */
const S = {
  mode: 'overview', data: null, room: null,
  pos: new THREE.Vector3(), yaw: 0, pitch: 0, vel: new THREE.Vector2(),
  keys: Object.create(null), joy: { x: 0, y: 0 }, tween: null,
};
let ceilings = [], roomMeshes = {}, viewTex = null, bgColor = new THREE.Color();
let walls = [], furniture = [];

/* ------------------------------------------------------------------ helpers */
function cssColor(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#eef0ed';
}
function setLoading(p, text) {
  $('loadBar').style.width = Math.round(p * 100) + '%';
  if (text) $('loadText').textContent = text;
}
function roomAt(x, z) {
  if (!S.data) return null;
  let hit = null;
  for (const r of S.data.rooms) for (const q of r.rects) {
    if (x >= q[0] - 0.02 && x <= q[2] + 0.02 && z >= q[1] - 0.02 && z <= q[3] + 0.02) { if (!hit || r.id === 'loggia') hit = r; }
  }
  return hit;
}
function roomCenter(r) {
  let a = 0, cx = 0, cz = 0;
  for (const q of r.rects) { const w = (q[2] - q[0]) * (q[3] - q[1]); a += w; cx += (q[0] + q[2]) / 2 * w; cz += (q[1] + q[3]) / 2 * w; }
  return new THREE.Vector3(cx / a, 0, cz / a);
}

/* ------------------------------------------------------------------ materials: lightmaps without double-counting IBL diffuse */
const noIblDiffuseChunk = THREE.ShaderChunk.lights_fragment_maps.replace('iblIrradiance += getIBLIrradiance( geometryNormal );', '');
function patchLightmapped(m) {
  m.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <lights_fragment_maps>', noIblDiffuseChunk); };
  m.customProgramCacheKey = () => 'lightmapped';
}

/* ------------------------------------------------------------------ loading */
async function load() {
  setLoading(0.02, 'Loading the floor plan…');
  S.data = await (await fetch('data/scene.json')).json();
  buildUI();
  const texLoader = new THREE.TextureLoader();
  const lmEntries = Object.entries(S.data.lightmaps || {});
  const lightmaps = {};
  let done = 0;
  const lmPromise = Promise.all(lmEntries.map(async ([room, info]) => {
    const t = await texLoader.loadAsync(info.file);
    t.flipY = false;
    t.colorSpace = THREE.SRGBColorSpace;
    t.channel = 1;
    t.anisotropy = 4;
    lightmaps[room] = t;
    done++;
  }));
  const viewPromise = texLoader.loadAsync('assets/view.jpg').then(t => {
    t.mapping = THREE.EquirectangularReflectionMapping;
    t.colorSpace = THREE.SRGBColorSpace;
    viewTex = t;
    // the Blender panorama is centred on plan-north (-Z here); rotate it so the river lies outside the windows
    scene.backgroundRotation.set(0, Math.PI / 2, 0);
    scene.backgroundIntensity = 1.15;
  }).catch(() => null);
  const draco = new DRACOLoader().setDecoderPath('vendor/three/addons/libs/draco/gltf/').setDecoderConfig({ type: 'wasm' });
  const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync(S.data.model || 'assets/flat.glb', e => {
    if (e.total) setLoading(0.05 + 0.8 * e.loaded / e.total, `Loading the model… ${Math.round(e.loaded / 1e6)} / ${Math.round(e.total / 1e6)} MB`);
  });
  setLoading(0.88, 'Lighting the rooms…');
  await lmPromise;
  await viewPromise;
  prepare(gltf.scene, lightmaps);
  scene.add(gltf.scene);
  buildProbes();
  setLoading(1, 'Ready');
  $('loading').hidden = true;
  const start = (location.hash || '').replace('#', '');
  setMode(['walk', 'plan', 'overview'].includes(start) ? start : 'overview', true);
}

function prepare(root, lightmaps) {
  const inherit = ['room', 'lightmap', 'kind', 'solid'];
  root.traverse(o => {
    if (o.parent) for (const k of inherit) if (o.userData[k] === undefined && o.parent.userData[k] !== undefined) o.userData[k] = o.parent.userData[k];
    if (!o.isMesh) return;
    const room = o.userData.room || null;
    const m = o.material.clone();
    o.material = m;
    const lm = room && o.userData.lightmap && lightmaps[room] && o.geometry.attributes.uv1;
    if (lm) {
      m.lightMap = lightmaps[room];
      m.lightMapIntensity = (S.data.lmMax || 4) * Math.PI * LM_GAIN;
      patchLightmapped(m);
    }
    if (m.emissive && m.emissive.getHex() !== 0) m.emissiveIntensity *= EMISSIVE_GAIN;
    if (m.transparent) { m.depthWrite = false; o.renderOrder = 2; }
    if (m.map) m.map.anisotropy = 8;
    o.userData.lm = !!lm;
    if (o.userData.kind === 'ceiling') ceilings.push(o);
    const key = room || '_none';
    (roomMeshes[key] = roomMeshes[key] || []).push(o);
  });
  walls = S.data.walls.map(w => ({ x0: w[0], z0: w[1], x1: w[2], z1: w[3] }));
  furniture = S.data.furniture.map(w => ({ x0: w[0], z0: w[1], x1: w[2], z1: w[3], name: w[4] }));
}

function buildProbes() {
  const pmrem = new THREE.PMREMGenerator(renderer);
  const rt = new THREE.WebGLCubeRenderTarget(192, { type: THREE.HalfFloatType });
  const cube = new THREE.CubeCamera(0.05, 100, rt);
  scene.background = viewTex || new THREE.Color(0xdfe7ec);
  for (const c of ceilings) c.visible = true;
  const probes = {};
  for (const r of S.data.rooms) {
    const c = roomCenter(r);
    cube.position.set(c.x, 1.35, c.z);
    cube.update(renderer, scene);
    probes[r.id] = pmrem.fromCubemap(rt.texture).texture;
  }
  const centers = S.data.rooms.map(r => [r.id, roomCenter(r)]);
  for (const [key, list] of Object.entries(roomMeshes)) {
    for (const o of list) {
      let id = key;
      if (!probes[id]) {
        const p = new THREE.Vector3();
        o.getWorldPosition(p);
        id = centers.reduce((b, [k, c]) => (c.distanceTo(p) < b[1] ? [k, c.distanceTo(p)] : b), ['living', 1e9])[0];
      }
      o.material.envMap = probes[id];
      o.material.envMapIntensity = o.userData.lm ? 1.0 : 0.9;
      o.material.needsUpdate = true;
    }
  }
  rt.dispose();
  pmrem.dispose();
}

/* ------------------------------------------------------------------ UI */
function buildUI() {
  const d = S.data;
  const loggia = d.rooms.find(r => r.id === 'loggia');
  $('statArea').textContent = d.netArea.toFixed(1);
  $('statCeil').textContent = d.ceiling.toFixed(2);
  if (loggia) $('statLoggia').textContent = loggia.area.toFixed(1);
  $('sheetArea').textContent = `${d.netArea.toFixed(1)} m² · rooms`;
  const ul = $('roomList');
  ul.innerHTML = '';
  for (const r of d.rooms) {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.dataset.room = r.id;
    b.innerHTML = `<span><span class="nm"></span><span class="hu"></span></span><span class="ar"></span>`;
    b.querySelector('.nm').textContent = r.name;
    b.querySelector('.hu').textContent = r.hu;
    b.querySelector('.ar').textContent = r.area.toFixed(1) + ' m²';
    b.addEventListener('click', () => goRoom(r.id));
    li.appendChild(b);
    ul.appendChild(li);
  }
  buildMini();
  const tags = $('tags');
  tags.innerHTML = '';
  for (const r of d.rooms) {
    const t = document.createElement('button');
    t.className = 'tag';
    t.dataset.room = r.id;
    t.innerHTML = '<b></b><span></span>';
    t.querySelector('b').textContent = r.name;
    t.querySelector('span').textContent = r.area.toFixed(1) + ' m²';
    t.setAttribute('aria-label', `Walk into the ${r.name.toLowerCase()}`);
    t.addEventListener('click', () => goRoom(r.id));
    tags.appendChild(t);
    r._tag = t;
    const big = r.rects.reduce((a, q) => ((q[2] - q[0]) * (q[3] - q[1]) > (a[2] - a[0]) * (a[3] - a[1]) ? q : a));
    r._c = new THREE.Vector3((big[0] + big[2]) / 2, 0, (big[1] + big[3]) / 2);
  }
}

const _v = new THREE.Vector3();
function updateTags() {
  const show = S.mode !== 'walk';
  const w = stage.clientWidth, h = stage.clientHeight;
  const placed = [];
  const rooms = [...S.data.rooms].sort((a, b) => b.area - a.area);
  for (const r of rooms) {
    const t = r._tag;
    if (!t) continue;
    if (!show) { t.hidden = true; continue; }
    _v.set(r._c.x, r.id === 'loggia' ? 1.2 : 1.9, r._c.z).project(camera);
    const vis = _v.z < 1 && Math.abs(_v.x) < 1.05 && Math.abs(_v.y) < 1.05;
    t.hidden = !vis;
    if (!vis) continue;
    if (!t._w) { t._w = t.offsetWidth || 90; t._h = t.offsetHeight || 26; }
    let x = (_v.x * 0.5 + 0.5) * w, y = (-_v.y * 0.5 + 0.5) * h;
    // nudge small-room labels so they do not sit on top of each other
    for (let k = 0; k < 6; k++) {
      const hit = placed.find(p => Math.abs(p.x - x) < (p.w + t._w) / 2 + 4 && Math.abs(p.y - y) < (p.h + t._h) / 2 + 3);
      if (!hit) break;
      y = hit.y + (y >= hit.y ? 1 : -1) * ((hit.h + t._h) / 2 + 4);
    }
    placed.push({ x, y, w: t._w, h: t._h });
    t.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
  }
}

function buildMini() {
  const d = S.data, [x0, z0, x1, z1] = d.bounds, pad = 0.25;
  const svg = $('miniSvg');
  const ns = 'http://www.w3.org/2000/svg';
  svg.setAttribute('viewBox', `${x0 - pad} ${z0 - pad} ${x1 - x0 + 2 * pad} ${z1 - z0 + 2 * pad}`);
  svg.innerHTML = '';
  const el = (t, a) => { const e = document.createElementNS(ns, t); for (const k in a) e.setAttribute(k, a[k]); svg.appendChild(e); return e; };
  for (let x = Math.ceil(x0); x <= x1; x++) el('line', { x1: x, y1: z0 - pad, x2: x, y2: z1 + pad, class: 'grid' });
  for (let z = Math.ceil(z0); z <= z1; z++) el('line', { x1: x0 - pad, y1: z, x2: x1 + pad, y2: z, class: 'grid' });
  for (const r of d.rooms) for (const q of r.rects) el('rect', { x: q[0], y: q[1], width: q[2] - q[0], height: q[3] - q[1], class: 'rm', 'data-room': r.id });
  for (const w of d.walls) el('rect', { x: w[0], y: w[1], width: w[2] - w[0], height: w[3] - w[1], class: 'wl' });
  const g = el('g', { id: 'me' });
  const cone = document.createElementNS(ns, 'path');
  cone.setAttribute('d', 'M0 0 L-0.9 -1.6 A1.85 1.85 0 0 1 0.9 -1.6 Z');
  cone.setAttribute('class', 'cone');
  g.appendChild(cone);
  const dot = document.createElementNS(ns, 'circle');
  dot.setAttribute('r', '0.22');
  dot.setAttribute('class', 'me');
  g.appendChild(dot);
  svg.addEventListener('click', e => {
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM().inverse());
    const r = roomAt(p.x, p.y);
    if (!r) return;
    const [fx, fz] = freeSpot(p.x, p.y);
    if (S.mode !== 'walk') setMode('walk');
    S.pos.set(fx, 0, fz);
  });
}

function updateMini() {
  const g = $('me');
  if (!g) return;
  const show = S.mode === 'walk';
  g.style.display = show ? '' : 'none';
  if (show) g.setAttribute('transform', `translate(${S.pos.x} ${S.pos.z}) rotate(${-S.yaw * 180 / Math.PI})`);
  const id = S.room ? S.room.id : null;
  document.querySelectorAll('#miniSvg .rm').forEach(r => r.classList.toggle('on', r.dataset.room === id));
  document.querySelectorAll('#roomList button').forEach(b => b.classList.toggle('on', b.dataset.room === id));
}

const HINTS = {
  overview: 'Drag to orbit · scroll or pinch to zoom · pick a room to walk in',
  walk: matchMedia('(pointer: coarse)').matches
    ? 'Left thumb to move · drag to look around'
    : '<kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> move · drag to look · <kbd>Shift</kbd> walk faster · click the map to jump',
  plan: 'Drag to pan · scroll or pinch to zoom · click a room to walk in',
};

function setMode(mode, instant) {
  S.mode = mode;
  document.querySelectorAll('.modes button').forEach(b => {
    const on = b.dataset.mode === mode;
    b.classList.toggle('on', on);
    b.setAttribute('aria-selected', on);
  });
  orbit.enabled = mode === 'overview';
  planCtl.enabled = mode === 'plan';
  for (const c of ceilings) c.visible = mode === 'walk';
  camera = mode === 'walk' ? camWalk : mode === 'plan' ? camPlan : camOrbit;
  scene.background = mode === 'walk' && viewTex ? viewTex : bgColor;
  $('hint').innerHTML = HINTS[mode];
  $('joy').hidden = !(mode === 'walk' && matchMedia('(pointer: coarse)').matches);
  $('planBtn').textContent = mode === 'plan' ? 'Back to the overview' : 'Show the floor plan';
  if (mode === 'walk' && S.pos.lengthSq() === 0) placeAt(S.data.rooms.find(r => r.id === 'living') || S.data.rooms[0], true);
  if (mode === 'overview' && (instant || !S.orbitInit)) resetOverview();
  if (mode === 'plan') resetPlan();
  if (mode !== 'walk' && document.pointerLockElement) document.exitPointerLock();
  try { history.replaceState(null, '', '#' + mode); } catch (e) { /* sandboxed */ }
  updateWhere();
}

function resetOverview() {
  const [x0, z0, x1, z1] = S.data.bounds;
  const c = new THREE.Vector3((x0 + x1) / 2, 0.4, (z0 + z1) / 2);
  orbit.target.copy(c);
  const k = Math.max(1, 0.8 / Math.max(0.3, camOrbit.aspect));   // back off on narrow portrait screens
  camOrbit.position.set(c.x + 7.5 * k, 13.5 * k, c.z + 9.5 * k);
  orbit.update();
  S.orbitInit = true;
}

function fitPlan() {
  const [x0, z0, x1, z1] = S.data.bounds;
  const w = stage.clientWidth, h = stage.clientHeight, a = w / h;
  const half = Math.max((z1 - z0) / 2 + 0.6, ((x1 - x0) / 2 + 0.6) / a);
  camPlan.left = -half * a;
  camPlan.right = half * a;
  camPlan.top = half;
  camPlan.bottom = -half;
  camPlan.updateProjectionMatrix();
}
function resetPlan() {
  const [x0, z0, x1, z1] = S.data.bounds;
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  camPlan.position.set(cx, 30, cz);
  camPlan.up.set(0, 0, -1);
  camPlan.zoom = 1;
  planCtl.target.set(cx, 0, cz);
  camPlan.lookAt(cx, 0, cz);
  fitPlan();
  planCtl.update();
}

function placeAt(r, instant) {
  const [x, z, yaw] = r.spawn;
  const [fx, fz] = freeSpot(x, z);
  if (instant || reduceMotion) {
    S.pos.set(fx, 0, fz);
    S.yaw = yaw;
    S.pitch = 0;
    return;
  }
  S.tween = { t: 0, from: S.pos.clone(), to: new THREE.Vector3(fx, 0, fz), y0: S.yaw, y1: nearAngle(S.yaw, yaw), p0: S.pitch };
}
function nearAngle(a, b) {
  while (b - a > Math.PI) b -= 2 * Math.PI;
  while (b - a < -Math.PI) b += 2 * Math.PI;
  return b;
}

function goRoom(id) {
  const r = S.data.rooms.find(q => q.id === id);
  if (!r) return;
  if (S.mode !== 'walk') { setMode('walk'); placeAt(r, true); } else placeAt(r);
  if (matchMedia('(max-width: 820px)').matches) collapseSheet(true);
}

function updateWhere() {
  if (S.mode === 'walk' && S.room) {
    $('whereName').textContent = S.room.name;
    $('whereHu').textContent = `${S.room.hu} · ${S.room.area.toFixed(1)} m²`;
  } else if (S.mode === 'plan') {
    $('whereName').textContent = 'Floor plan';
    $('whereHu').textContent = `${S.data.netArea.toFixed(1)} m² + loggia`;
  } else {
    $('whereName').textContent = 'Overview';
    $('whereHu').textContent = 'All rooms, ceilings removed';
  }
}

/* ------------------------------------------------------------------ collisions */
function blocked(x, z) {
  for (const b of walls) if (x > b.x0 - RADIUS && x < b.x1 + RADIUS && z > b.z0 - RADIUS && z < b.z1 + RADIUS) return true;
  for (const b of furniture) if (x > b.x0 - RADIUS * 0.6 && x < b.x1 + RADIUS * 0.6 && z > b.z0 - RADIUS * 0.6 && z < b.z1 + RADIUS * 0.6) return true;
  return !roomAt(x, z);
}
function freeSpot(x, z) {
  if (!blocked(x, z)) return [x, z];
  for (let r = 0.05; r < 1.5; r += 0.05) for (let a = 0; a < 6.283; a += 0.35) {
    const nx = x + Math.cos(a) * r, nz = z + Math.sin(a) * r;
    if (!blocked(nx, nz)) return [nx, nz];
  }
  return [x, z];
}
function moveBy(dx, dz) {
  const p = S.pos;
  if (!blocked(p.x + dx, p.z)) p.x += dx; else S.vel.x *= 0.3;
  if (!blocked(p.x, p.z + dz)) p.z += dz; else S.vel.y *= 0.3;
}

/* ------------------------------------------------------------------ input */
document.querySelectorAll('.modes button').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));
$('resetBtn').addEventListener('click', () => {
  if (S.mode === 'overview') resetOverview();
  else if (S.mode === 'plan') resetPlan();
  else placeAt(S.room || S.data.rooms[0]);
});
$('planBtn').addEventListener('click', () => setMode(S.mode === 'plan' ? 'overview' : 'plan'));
function collapseSheet(c) {
  $('side').classList.toggle('collapsed', c);
  $('sheetToggle').setAttribute('aria-expanded', String(!c));
}
$('sheetToggle').addEventListener('click', () => collapseSheet(!$('side').classList.contains('collapsed')));
if (matchMedia('(max-width: 820px)').matches) collapseSheet(true);

addEventListener('keydown', e => {
  if (e.target.closest && e.target.closest('input, textarea')) return;
  S.keys[e.code] = true;
  if (S.mode === 'walk' && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
});
addEventListener('keyup', e => { S.keys[e.code] = false; });
addEventListener('blur', () => { S.keys = Object.create(null); });

const pointers = new Map();
const joyEl = $('joy'), knob = joyEl.firstElementChild;
canvas.addEventListener('pointerdown', e => {
  if (S.mode !== 'walk') return;
  canvas.setPointerCapture(e.pointerId);
  const r = canvas.getBoundingClientRect();
  const joy = e.pointerType === 'touch' && e.clientX - r.left < r.width * 0.42 && e.clientY - r.top > r.height * 0.35;
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY, sx: e.clientX, sy: e.clientY, joy, moved: 0 });
  if (joy) {
    joyEl.style.left = (e.clientX - r.left - 58) + 'px';
    joyEl.style.top = (e.clientY - r.top - 58) + 'px';
    joyEl.style.bottom = 'auto';
  }
});
canvas.addEventListener('pointermove', e => {
  const p = pointers.get(e.pointerId);
  if (S.mode !== 'walk') return;
  const locked = document.pointerLockElement === canvas;
  if (!p && !locked) return;
  const dx = locked ? e.movementX : e.clientX - p.x;
  const dy = locked ? e.movementY : e.clientY - p.y;
  if (p) { p.moved += Math.abs(dx) + Math.abs(dy); p.x = e.clientX; p.y = e.clientY; }
  if (p && p.joy) {
    const jx = Math.max(-1, Math.min(1, (p.x - p.sx) / 46)), jy = Math.max(-1, Math.min(1, (p.y - p.sy) / 46));
    S.joy.x = jx;
    S.joy.y = jy;
    knob.style.transform = `translate(${jx * 30}px, ${jy * 30}px)`;
    return;
  }
  const k = e.pointerType === 'touch' ? 0.0055 : 0.0038;
  S.yaw -= dx * k;
  S.pitch = Math.max(-1.25, Math.min(1.25, S.pitch - dy * k));
  S.tween = null;
});
function endPointer(e) {
  const p = pointers.get(e.pointerId);
  if (!p) return;
  pointers.delete(e.pointerId);
  if (p.joy) {
    S.joy.x = S.joy.y = 0;
    knob.style.transform = '';
    joyEl.style.left = '';
    joyEl.style.top = '';
    joyEl.style.bottom = '';
  }
}
canvas.addEventListener('pointerup', endPointer);
canvas.addEventListener('pointercancel', endPointer);
canvas.addEventListener('dblclick', () => {
  if (S.mode !== 'walk') return;
  try { const pr = canvas.requestPointerLock(); if (pr && pr.catch) pr.catch(() => {}); } catch (e) { /* not available */ }
});
// click in plan view: walk to that spot
let downAt = null;
canvas.addEventListener('pointerdown', e => { downAt = [e.clientX, e.clientY]; }, true);
canvas.addEventListener('click', e => {
  if (S.mode !== 'plan' || !downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 5) return;
  const r = canvas.getBoundingClientRect();
  const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  const ray = new THREE.Raycaster();
  ray.setFromCamera(ndc, camPlan);
  const hit = ray.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), new THREE.Vector3());
  if (!hit || !roomAt(hit.x, hit.z)) return;
  setMode('walk');
  const [fx, fz] = freeSpot(hit.x, hit.z);
  S.pos.set(fx, 0, fz);
});

/* ------------------------------------------------------------------ resize, theme */
function resize() {
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setSize(w, h, false);
  camWalk.aspect = camOrbit.aspect = w / h;
  camWalk.updateProjectionMatrix();
  camOrbit.updateProjectionMatrix();
  if (S.data) fitPlan();
}
new ResizeObserver(resize).observe(stage);
function readTheme() {
  bgColor.set(cssColor('--bg'));
  if (S.mode !== 'walk') scene.background = bgColor;
}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', readTheme);
new MutationObserver(readTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
readTheme();
resize();

/* ------------------------------------------------------------------ loop */
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  if (S.data) {
    if (S.mode === 'walk') stepWalk(dt);
    else if (S.mode === 'overview') orbit.update();
    else planCtl.update();
    updateMini();
    updateTags();
  }
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
function stepWalk(dt) {
  if (S.tween) {
    const t = S.tween;
    t.t = Math.min(1, t.t + dt / 0.7);
    const e = t.t < 0.5 ? 2 * t.t * t.t : 1 - Math.pow(-2 * t.t + 2, 2) / 2;
    S.pos.lerpVectors(t.from, t.to, e);
    S.yaw = t.y0 + (t.y1 - t.y0) * e;
    S.pitch = t.p0 * (1 - e);
    if (t.t >= 1) S.tween = null;
  } else {
    const k = S.keys;
    let f = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0) - S.joy.y;
    let s = (k.KeyD ? 1 : 0) - (k.KeyA ? 1 : 0) + S.joy.x;
    if (k.ArrowLeft) S.yaw += 1.8 * dt;
    if (k.ArrowRight) S.yaw -= 1.8 * dt;
    if (k.KeyQ) S.yaw += 1.8 * dt;
    if (k.KeyE) S.yaw -= 1.8 * dt;
    const len = Math.hypot(f, s);
    if (len > 1) { f /= len; s /= len; }
    const speed = (k.ShiftLeft || k.ShiftRight) ? 2.6 : 1.35;
    const sy = Math.sin(S.yaw), cy = Math.cos(S.yaw);
    const tx = (-sy * f + cy * s) * speed, tz = (-cy * f - sy * s) * speed;
    const a = 1 - Math.exp(-dt * 10);
    S.vel.x += (tx - S.vel.x) * a;
    S.vel.y += (tz - S.vel.y) * a;
    moveBy(S.vel.x * dt, S.vel.y * dt);
  }
  camWalk.position.set(S.pos.x, EYE, S.pos.z);
  camWalk.rotation.set(S.pitch, S.yaw, 0);
  const r = roomAt(S.pos.x, S.pos.z);
  if (r !== S.room) { S.room = r; updateWhere(); }
}
requestAnimationFrame(frame);

load().catch(err => {
  console.error(err);
  $('loadText').textContent = 'The model could not be loaded. Serve this folder over http (for example: python3 -m http.server) and reload.';
});

window.flat = { S, setMode, goRoom, renderer, scene };
