// Interactive objects: the pieces exported with a "dynamic" flag become Rapier rigid bodies.
// Walk into them to shove them aside; drag one with the pointer to pick it up, carry it while you
// walk, and let go to drop or throw it. The grab follows image-blaster's approach: a kinematic
// "hand" body that the object hangs from on a ball joint, with damping and speed limits.
import * as THREE from 'three';
import RAPIER from 'rapier';

const STEP = 1 / 60;
const LINEAR_LIMIT = 5;        // m/s while held or thrown
const ANGULAR_LIMIT = 10;      // rad/s
const REACH = 3.2;             // how far away you can pick things up (m)
const HAND_MIN = 0.45, HAND_MAX = 2.6;
// collision groups (membership << 16 | filter). The walker's body never shoves objects in the simulation itself
// (a moving kinematic body pushes with unlimited force and can squeeze a chair through a wall); instead the
// character controller in walk() pushes them with finite impulses and stops when they will not move.
const ITEM = (0x0001 << 16) | 0xffff, PLAYER = (0x0002 << 16) | 0xfffe, WALKER_QUERY = (0x0002 << 16) | 0x0001;

let ready = null;
export async function createPhysics(opts) {
  if (!ready) ready = RAPIER.init();
  await ready;
  return new Physics(opts);
}

const _p = new THREE.Vector3(), _q = new THREE.Quaternion(), _qi = new THREE.Quaternion(), _e = new THREE.Euler();
const v3 = v => ({ x: v.x, y: v.y, z: v.z });

class Physics {
  constructor({ scene, data, dynamic, meshColliders }) {
    this.scene = scene;
    this.world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
    this.world.timestep = STEP;
    this.acc = 0;
    this.items = [];
    this.byCollider = new Map();
    this.grab = null;
    this.lastWalker = null;
    this.moved = false;

    // the flat: floor, ceiling, walls and the furniture footprints (their real heights)
    const H = data.ceiling || 2.6;
    const [x0, z0, x1, z1] = data.bounds;
    const fixed = this.world.createRigidBody(RAPIER.RigidBodyDesc.fixed());
    const box = (cx, cy, cz, hx, hy, hz, friction = 0.7) =>
      this.world.createCollider(RAPIER.ColliderDesc.cuboid(hx, hy, hz).setTranslation(cx, cy, cz).setFriction(friction), fixed);
    const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, hx = (x1 - x0) / 2 + 2, hz = (z1 - z0) / 2 + 2;
    box(cx, -0.1, cz, hx, 0.1, hz, 0.9);
    box(cx, H + 0.1, cz, hx, 0.1, hz);
    for (const w of data.walls) box((w[0] + w[2]) / 2, H / 2, (w[1] + w[3]) / 2, (w[2] - w[0]) / 2, H / 2, (w[3] - w[1]) / 2, 0.5);
    const own = new Set([...dynamic, ...meshColliders].map(o => o.name));
    for (const f of data.furniture) {
      if (own.has(f[4])) continue;
      const y0 = f[5] ?? 0, y1 = f[6] ?? 0.75;
      box((f[0] + f[2]) / 2, (y0 + y1) / 2, (f[1] + f[3]) / 2, (f[2] - f[0]) / 2, Math.max(0.01, (y1 - y0) / 2), (f[3] - f[1]) / 2);
    }
    // pieces whose real shape matters (the sofa's seat, the table top): exact triangle colliders
    for (const o of meshColliders) {
      const { vertices, indices } = worldTriangles(o);
      if (indices.length) this.world.createCollider(RAPIER.ColliderDesc.trimesh(vertices, indices).setFriction(0.8), fixed);
    }

    // the walker: a kinematic capsule that shoulders objects out of the way
    this.player = this.world.createRigidBody(RAPIER.RigidBodyDesc.kinematicPositionBased().setTranslation(0, -20, 0));
    this.playerCollider = this.world.createCollider(RAPIER.ColliderDesc.capsule(0.55, 0.2).setFriction(0.2).setCollisionGroups(PLAYER), this.player);
    this.cc = this.world.createCharacterController(0.01);
    this.cc.setApplyImpulsesToDynamicBodies(true);
    this.cc.setCharacterMass(70);
    this.cc.setSlideEnabled(true);
    // the hand that held objects hang from
    this.hand = this.world.createRigidBody(RAPIER.RigidBodyDesc.kinematicPositionBased().setTranslation(0, -20, 0));

    const skip = new Set([this.player.handle, this.hand.handle]);
    this.notMe = c => { const b = c.parent(); return !b || !skip.has(b.handle); };   // rays ignore the walker and the hand
    this.shadowTex = blobTexture();
    for (const o of dynamic) this.add(o);
  }

  add(o) {
    o.updateWorldMatrix(true, true);
    o.getWorldPosition(_p);
    o.getWorldQuaternion(_q);
    // points of the mesh in the body's frame (position + rotation, the object's scale stays in the points)
    const pts = [], inv = _qi.copy(_q).invert(), w = new THREE.Vector3();
    const lo = new THREE.Vector3(Infinity, Infinity, Infinity), hi = lo.clone().negate();
    o.traverse(m => {
      if (!m.isMesh) return;
      const pos = m.geometry.attributes.position, step = Math.max(1, Math.floor(pos.count / 3000));
      for (let i = 0; i < pos.count; i += step) {
        w.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld).sub(_p).applyQuaternion(inv);
        pts.push(w.x, w.y, w.z);
        lo.min(w); hi.max(w);
      }
    });
    const ud = o.userData;
    const body = this.world.createRigidBody(RAPIER.RigidBodyDesc.dynamic()
      .setTranslation(_p.x, _p.y, _p.z).setRotation(v4(_q))
      .setLinearDamping(0.45).setAngularDamping(0.35).setCcdEnabled(true));
    const desc = (RAPIER.ColliderDesc.convexHull(new Float32Array(pts)) ||
      RAPIER.ColliderDesc.cuboid((hi.x - lo.x) / 2, (hi.y - lo.y) / 2, (hi.z - lo.z) / 2)
        .setTranslation((hi.x + lo.x) / 2, (hi.y + lo.y) / 2, (hi.z + lo.z) / 2))
      .setMass(ud.mass || 1).setFriction(ud.friction ?? 0.7).setRestitution(ud.restitution ?? 0.12).setCollisionGroups(ITEM);
    const collider = this.world.createCollider(desc, body);
    // soft contact shadow that follows the object (it is not in the baked lighting)
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: this.shadowTex, transparent: true, depthWrite: false,
        opacity: 0.5, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -4 }));
    shadow.renderOrder = 1;
    shadow.raycast = () => {};
    this.scene.add(shadow);
    const item = { o, body, collider, shadow, size: hi.clone().sub(lo), lift: -lo.y,
      home: { p: _p.clone(), q: _q.clone() } };
    this.items.push(item);
    this.byCollider.set(collider.handle, item);
    o.traverse(m => { if (m.isMesh) m.userData.item = item; });
  }

  /** Let everything come to rest before it is shown, and remember that as each piece's home. */
  settleNow(seconds = 1.5) {
    for (let i = 0; i < seconds / STEP; i++) this.world.step();
    for (const it of this.items) {
      const t = it.body.translation(), r = it.body.rotation();
      it.home.p.set(t.x, t.y, t.z);
      it.home.q.set(r.x, r.y, r.z, r.w);
    }
    this.sync();
    this.moved = false;
  }

  /** How far the walker can really move this frame: objects in the way get pushed (by a 70 kg body), and stop
   *  you if they are stuck against a wall or the table. The walls themselves are handled by the viewer. */
  walk(dx, dz) {
    if (!this.lastWalker || (!dx && !dz)) return [dx, dz];
    this.cc.computeColliderMovement(this.playerCollider, { x: dx, y: 0, z: dz },
      RAPIER.QueryFilterFlags.EXCLUDE_FIXED | RAPIER.QueryFilterFlags.EXCLUDE_KINEMATIC, WALKER_QUERY);
    const m = this.cc.computedMovement();
    return [m.x, m.z];
  }

  /** Advance the simulation. walker: the walk-mode position (or null), aim: a ray for a held object. */
  step(dt, walker, aim) {
    this.acc = Math.min(this.acc + dt, STEP * 5);
    const n = Math.floor(this.acc / STEP);
    if (!n) return;
    this.acc -= n * STEP;
    // spread this frame's movement of the walker and the hand over the sub-steps
    const w0 = this.lastWalker, jump = walker && (!w0 || Math.hypot(walker.x - w0.x, walker.z - w0.z) > 0.5);
    if (!walker && w0) { this.player.setTranslation({ x: 0, y: -20, z: 0 }, true); this.lastWalker = null; }
    if (jump) this.player.setTranslation({ x: walker.x, y: 0.82, z: walker.z }, true);
    const g = this.grab;
    let from = null, to = null;
    if (g) {
      from = g.target.clone();
      to = aim ? aim.at(g.depth, new THREE.Vector3()) : from.clone();
      // throw velocity from the hand's recent motion (smoothed so a slow release does not fling things)
      const v = to.clone().sub(from).divideScalar(n * STEP);
      g.release.lerp(v, 0.5);
      if (g.release.length() > LINEAR_LIMIT) g.release.setLength(LINEAR_LIMIT);
      g.target.copy(to);
    }
    for (let k = 1; k <= n; k++) {
      const f = k / n;
      if (walker && !jump) this.player.setNextKinematicTranslation({ x: w0.x + (walker.x - w0.x) * f, y: 0.82, z: w0.z + (walker.z - w0.z) * f });
      if (g) {
        this.hand.setNextKinematicTranslation(v3(from.clone().lerp(to, f)));
        clamp(g.item.body);
      }
      this.world.step();
      if (g) clamp(g.item.body);
    }
    if (walker) this.lastWalker = { x: walker.x, z: walker.z };
    this.sync();
  }

  sync() {
    for (const it of this.items) {
      const t = it.body.translation(), r = it.body.rotation();
      it.o.position.set(t.x, t.y, t.z);
      it.o.quaternion.set(r.x, r.y, r.z, r.w);
      if (!this.moved && Math.hypot(t.x - it.home.p.x, t.y - it.home.p.y, t.z - it.home.p.z) > 0.05) this.moved = true;
      // shadow on whatever is underneath
      const hit = this.world.castRay(new RAPIER.Ray(t, { x: 0, y: -1, z: 0 }), 4, true, undefined, undefined, undefined, it.body,
        this.notMe);
      if (!hit) { it.shadow.visible = false; continue; }
      const ground = t.y - hit.timeOfImpact;
      const gap = Math.max(0, t.y - it.lift - ground);
      _e.setFromQuaternion(_q.set(r.x, r.y, r.z, r.w), 'YXZ');
      it.shadow.visible = true;
      it.shadow.position.set(t.x, ground + 0.004, t.z);
      it.shadow.rotation.set(0, _e.y, 0);
      const spread = 1.25 + gap * 0.8;
      it.shadow.scale.set(Math.max(0.15, it.size.x * spread), 1, Math.max(0.15, it.size.z * spread));
      it.shadow.material.opacity = 0.55 * Math.max(0, 1 - gap / 1.1);
    }
  }

  /** The object under a pointer ray, if it is in reach and nothing solid is in front of it. */
  pick(raycaster) {
    const meshes = [];
    for (const it of this.items) it.o.traverse(m => { if (m.isMesh) meshes.push(m); });
    const hit = raycaster.intersectObjects(meshes, false)[0];
    if (!hit || hit.distance > REACH) return null;
    const item = hit.object.userData.item;
    const ray = raycaster.ray;
    const block = this.world.castRay(new RAPIER.Ray(v3(ray.origin), v3(ray.direction)), hit.distance, true, undefined, undefined,
      undefined, item.body, this.notMe);
    if (block && block.timeOfImpact < hit.distance - 0.04) return null;
    return { item, point: hit.point, distance: hit.distance };
  }

  beginGrab(raycaster) {
    const p = this.pick(raycaster);
    if (!p) return false;
    this.endGrab();
    const { item, point } = p;
    const body = item.body;
    body.wakeUp();
    this.hand.setTranslation(v3(point), true);
    this.hand.setNextKinematicTranslation(v3(point));
    const t = body.translation(), r = body.rotation();
    const local = point.clone().sub(_p.set(t.x, t.y, t.z)).applyQuaternion(_qi.set(r.x, r.y, r.z, r.w).invert());
    const joint = this.world.createImpulseJoint(RAPIER.JointData.spherical({ x: 0, y: 0, z: 0 }, v3(local)), this.hand, body, true);
    body.setAngularDamping(3.0);
    this.grab = { item, joint, depth: Math.min(HAND_MAX, Math.max(HAND_MIN, p.distance)), target: point.clone(), release: new THREE.Vector3() };
    this.moved = true;
    return true;
  }

  /** Move the held object nearer or further (mouse wheel). */
  reach(delta) {
    if (this.grab) this.grab.depth = Math.min(HAND_MAX, Math.max(HAND_MIN, this.grab.depth + delta));
  }

  endGrab() {
    const g = this.grab;
    if (!g) return;
    this.grab = null;
    try { this.world.removeImpulseJoint(g.joint, true); } catch (e) { /* already gone */ }
    g.item.body.setAngularDamping(0.35);
    g.item.body.setLinvel(v3(g.release), true);
    clamp(g.item.body);
    g.item.body.wakeUp();
  }

  /** Put everything back where it was. */
  reset() {
    this.endGrab();
    for (const it of this.items) {
      it.body.setTranslation(v3(it.home.p), true);
      it.body.setRotation(v4(it.home.q), true);
      it.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
      it.body.setAngvel({ x: 0, y: 0, z: 0 }, true);
    }
    this.moved = false;
    this.sync();
  }

  dispose() {
    for (const it of this.items) {
      this.scene.remove(it.shadow);
      it.shadow.geometry.dispose();
      it.shadow.material.dispose();
    }
    this.shadowTex.dispose();
    this.world.removeCharacterController(this.cc);
    this.world.free();
    this.items = [];
  }
}

function v4(q) { return { x: q.x, y: q.y, z: q.z, w: q.w }; }

function clamp(body) {
  const l = body.linvel(), a = body.angvel();
  const ls = Math.hypot(l.x, l.y, l.z), as = Math.hypot(a.x, a.y, a.z);
  if (ls > LINEAR_LIMIT) body.setLinvel({ x: l.x * LINEAR_LIMIT / ls, y: l.y * LINEAR_LIMIT / ls, z: l.z * LINEAR_LIMIT / ls }, true);
  if (as > ANGULAR_LIMIT) body.setAngvel({ x: a.x * ANGULAR_LIMIT / as, y: a.y * ANGULAR_LIMIT / as, z: a.z * ANGULAR_LIMIT / as }, true);
}

function worldTriangles(o) {
  const v = [], idx = [];
  const w = new THREE.Vector3();
  o.updateWorldMatrix(true, true);
  o.traverse(m => {
    if (!m.isMesh) return;
    const g = m.geometry, pos = g.attributes.position, base = v.length / 3;
    for (let i = 0; i < pos.count; i++) { w.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); v.push(w.x, w.y, w.z); }
    if (g.index) for (let i = 0; i < g.index.count; i++) idx.push(base + g.index.getX(i));
    else for (let i = 0; i < pos.count; i++) idx.push(base + i);
  });
  return { vertices: new Float32Array(v), indices: new Uint32Array(idx) };
}

function blobTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.45, 'rgba(255,255,255,0.75)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g;
  x.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.NoColorSpace;
  return t;
}
