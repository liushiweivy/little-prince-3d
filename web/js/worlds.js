/* 多星球世界：B-612 + 旅途六小行星 + 地球。
 * 每个世界是一个定位在 center 的 Group，内容用本地坐标（球心在组原点）。
 * 明亮白昼天空、草地（实例化草叶）、NPC（混元 GLB）、金色出发台。 */
import * as THREE from '../vendor/three.module.min.js';
import { GLTFLoader } from '../vendor/loaders/GLTFLoader.js';
import { latLonToDir } from './sphere-math.js';
import { assetPath } from './assets.js';

const UP_Y = new THREE.Vector3(0, 1, 0);
const gltfLoader = new GLTFLoader();

const modelVariant = new URLSearchParams(location.search).get('model') === 'triposr'
  ? 'triposr' : 'hunyuan';
// 混元版玫瑰自带玻璃钟罩与底座（一体模型）；triposr 旧玫瑰仍配程序半球
const ROSE_FILE = modelVariant === 'triposr' ? './models/rose.glb' : './models/hunyuan-glass-dome.glb';
const ROSE_NEEDS_DOME = modelVariant === 'triposr';
const FOX_FILE = modelVariant === 'triposr' ? './models/fox.glb' : './models/hunyuan-fox.glb';
const ROSE_YAW = modelVariant === 'triposr' ? 0 : 0;
const FOX_YAW = modelVariant === 'triposr' ? -Math.PI / 2 : 0;

/* 世界布局：B-612 在原点，其余散在 80~170 外 */
export const WORLD_DEFS = [
  {
    id: 'b612', num: 'B-612', name: 'B-612 小行星',
    radius: 10, center: [0, 0, 0],
    palette: { base: 0x6fae4e, dark: 0x548c3e, accent: 0xdcc577 },
    grass: 1500, flowers: 90,
    pad: { lat: -16, lon: 150 },
    spawn: { lat: -16, lon: 150, face: { lat: 8, lon: 10 } },
    npcs: [
      { model: ROSE_FILE, yaw: ROSE_YAW, lat: 8, lon: 10, height: 0.9, label: '玫瑰', dome: ROSE_NEEDS_DOME, dialogue: 'rose' },
    ],
    props: [
      { model: './models/hunyuan-volcano-active.glb', height: 1.8, lat: -45, lon: 60, sink: 0.18, glow: 0xff5a1f },
      { model: './models/hunyuan-volcano-extinct.glb', height: 1.6, lat: -60, lon: 92, sink: 0.15 },
      { model: './models/hunyuan-baobab.glb', height: 2.4, lat: 40, lon: 120, sink: 0.06 },
      { model: './models/hunyuan-chair.glb', height: 0.9, lat: 24, lon: 66, yaw: 0.6 },          // 挪椅子看日落
      { model: './models/hunyuan-sheep-box.glb', height: 0.5, lat: -2, lon: 42, yaw: 0.3 },        // 画着羊的箱子
    ],
  },
  {
    id: 'king', num: '325', name: '325 号行星 · 国王',
    radius: 4.2, center: [-95, 28, -72],
    palette: { base: 0x8a74b8, dark: 0x6e5b9c, accent: 0xd9b56a },
    grass: 220, flowers: 0,
    pad: { lat: -18, lon: 10 },
    spawn: { lat: -18, lon: 10, face: { lat: 18, lon: 0 } },
    npcs: [{ model: './models/hunyuan-king.glb', yaw: 0, lat: 18, lon: 0, height: 1.0, label: '国王', dialogue: 'king' }],
    props: [
      { model: './models/hunyuan-throne.glb', height: 1.5, lat: 27, lon: 2, face: 'spawn' },
      { model: './models/hunyuan-fountain.glb', height: 1.0, lat: 2, lon: -18, sink: 0.05 }, // 王宫庭院喷泉
    ],
  },
  {
    id: 'vainman', num: '326', name: '326 号行星 · 爱虚荣的人',
    radius: 4.2, center: [88, 48, -92],
    palette: { base: 0xcf8fb0, dark: 0xb2749a, accent: 0xf0d88c },
    grass: 220, flowers: 14,
    pad: { lat: -18, lon: 10 },
    spawn: { lat: -18, lon: 10, face: { lat: 18, lon: 0 } },
    npcs: [{ model: './models/hunyuan-vainman.glb', yaw: 0, lat: 18, lon: 0, height: 0.98, label: '爱虚荣的人', dialogue: 'vainman' }],
  },
  {
    id: 'drunkard', num: '327', name: '327 号行星 · 酒鬼',
    radius: 4.2, center: [-72, -34, -108],
    palette: { base: 0x7c8a9e, dark: 0x637080, accent: 0xb8a878 },
    grass: 180, flowers: 0,
    pad: { lat: -18, lon: 10 },
    spawn: { lat: -18, lon: 10, face: { lat: 18, lon: 0 } },
    npcs: [{ model: './models/hunyuan-drunkard.glb', yaw: 0, lat: 18, lon: 0, height: 0.82, label: '酒鬼', dialogue: 'drunkard' }],
    props: [
      { model: './models/hunyuan-grapes.glb', height: 0.8, lat: 9, lon: -26, yaw: 1.2 }, // 葡萄→酒
      // 酒瓶空缺：2026-10-22 新生成的 hunyuan-wine-bottle.glb 是"底板浮雕瓶"（白瓶白底被理解成展示牌），未摆放，待换参考图重生成
    ],
  },
  {
    id: 'merchant', num: '328', name: '328 号行星 · 商人',
    radius: 4.2, center: [118, -12, -38],
    palette: { base: 0x5a9690, dark: 0x467a76, accent: 0xd9c878 },
    grass: 200, flowers: 0,
    pad: { lat: -18, lon: 10 },
    spawn: { lat: -18, lon: 10, face: { lat: 18, lon: 0 } },
    npcs: [{ model: './models/hunyuan-merchant.glb', yaw: 0, lat: 18, lon: 0, height: 0.98, label: '商人', dialogue: 'merchant' }],
  },
  {
    id: 'lamplighter', num: '329', name: '329 号行星 · 点灯人',
    radius: 3.6, center: [42, 84, -108],
    palette: { base: 0x55708f, dark: 0x41576f, accent: 0xe8c25a },
    grass: 160, flowers: 0,
    pad: { lat: -22, lon: 8 },
    spawn: { lat: -22, lon: 8, face: { lat: 16, lon: 0 } },
    npcs: [{ model: './models/hunyuan-lamplighter.glb', yaw: 0, lat: 16, lon: 0, height: 0.92, label: '点灯人', dialogue: 'lamplighter' }],
    props: [
      { model: './models/hunyuan-streetlamp.glb', height: 2.1, lat: 9, lon: -16 },
    ],
  },
  {
    id: 'geographer', num: '330', name: '330 号行星 · 地理学家',
    radius: 4.6, center: [-118, 58, 26],
    palette: { base: 0xb39a6e, dark: 0x94805a, accent: 0x6fae4e },
    grass: 240, flowers: 10,
    pad: { lat: -18, lon: 10 },
    spawn: { lat: -18, lon: 10, face: { lat: 18, lon: 0 } },
    npcs: [{ model: './models/hunyuan-geographer.glb', yaw: 0, lat: 18, lon: 0, height: 1.05, label: '地理学家', dialogue: 'geographer' }],
    props: [
      { model: './models/hunyuan-globe.glb', height: 0.85, lat: 10, lon: -22, yaw: 0.4 },
      { model: './models/hunyuan-giant-book.glb', height: 0.95, lat: 4, lon: 20, yaw: -0.5 },
    ],
  },
  {
    id: 'earth', num: '地球', name: '地球 · 撒哈拉沙漠',
    radius: 7, center: [64, -72, 132],
    palette: { base: 0xdcc07e, dark: 0xc8a85e, accent: 0xe8d8a8 },
    grass: 0, flowers: 0,
    pad: { lat: 4, lon: 150 },
    spawn: { lat: 4, lon: 150, face: { lat: 12, lon: -140 } },
    npcs: [
      { model: './models/hunyuan-pilot.glb', yaw: 0, lat: 12, lon: -140, height: 1.0, label: '飞行员', dialogue: 'pilot' },
      { model: './models/hunyuan-snake.glb', yaw: 0, lat: -8, lon: 40, height: 0.6, label: '蛇', dialogue: 'snake' },
      // 狐狸在地球的麦田（原著：穿越沙漠后在麦田相遇）
      { model: FOX_FILE, yaw: FOX_YAW, lat: 24, lon: -66, height: 0.72, label: '狐狸', dialogue: 'fox' },
    ],
    props: [
      { model: './models/hunyuan-plane-wreck.glb', height: 1.9, lat: -6, lon: -148, yaw: 0.8 }, // 坠机点
      { model: './models/hunyuan-well.glb', height: 1.2, lat: 20, lon: -155 }, // 沙漠水井（原著结局）
      { model: './models/hunyuan-wooden-bench.glb', height: 0.9, lat: 22, lon: -54, face: { lat: 24, lon: -66 }, yaw: Math.PI }, // 麦海边的长椅（模型 +Z 朝靠背，转 180° 面朝狐狸）
    ],
    wheat: { lat: 24, lon: -66 },
  },
];

/* 确定性伪随机，草/石头每次加载分布一致 */
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function dirToLocal(radius, latDeg, lonDeg, sink = 0) {
  const d = latLonToDir(latDeg, lonDeg);
  return new THREE.Vector3(d.x, d.y, d.z).multiplyScalar(radius - sink);
}

/* 把物体放到球面 lat/lon，本地 Y 轴对齐法线 */
function placeOnSphere(obj, radius, latDeg, lonDeg, sink = 0) {
  const p = dirToLocal(radius, latDeg, lonDeg, sink);
  obj.position.copy(p);
  obj.quaternion.setFromUnitVectors(UP_Y, p.clone().normalize());
  return obj;
}

/* 球面锚点：本地 Y 对齐法线，本地 +Z 朝向 faceLatLon（让 NPC 面向玩家来路） */
function makeFacingAnchor(radius, lat, lon, faceLatLon, sink = 0.02) {
  const g = new THREE.Group();
  const n = latLonToDirVec(lat, lon);
  let f = latLonToDirVec(faceLatLon.lat, faceLatLon.lon);
  f.addScaledVector(n, -f.dot(n)); // 投影到 NPC 切平面
  if (f.lengthSq() < 1e-8) f.set(0, 0, 1).addScaledVector(n, -n.z);
  f.normalize();
  const x = new THREE.Vector3().crossVectors(n, f);
  g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, n.clone(), f));
  g.position.copy(n).multiplyScalar(radius - sink);
  return g;
}

/* GLB 归一化：先偏航再量盒（旋转绕自身原点，否则非对称模型会被居中偏移带离锚点）、
 * XZ 居中、底贴 y=0、高 = targetHeight */
function normalizeProp(obj, targetHeight, yaw = 0) {
  obj.rotation.y = yaw;
  const box = new THREE.Box3().setFromObject(obj);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const s = targetHeight / size.y;
  const wrap = new THREE.Group();
  obj.position.set(-center.x * s, -box.min.y * s, -center.z * s);
  obj.scale.setScalar(s);
  wrap.add(obj);
  return wrap;
}

function makeGround(radius, palette) {
  // detail 5：20480 三角面/星（detail 6 是 81920），flatShading 风格下肉眼无差
  const geo = new THREE.IcosahedronGeometry(radius, 5);
  const posAttr = geo.getAttribute('position');
  const colors = new Float32Array(posAttr.count * 3);
  const base = new THREE.Color(palette.base);
  const dark = new THREE.Color(palette.dark);
  const accent = new THREE.Color(palette.accent);
  const c = new THREE.Color();
  for (let i = 0; i < posAttr.count; i++) {
    const x = posAttr.getX(i), y = posAttr.getY(i), z = posAttr.getZ(i);
    const n = Math.sin(x * 1.7) * Math.cos(z * 1.3) + Math.sin(y * 2.1 + x);
    c.copy(base).lerp(n > 0 ? dark : accent, Math.min(0.42, Math.abs(n) * 0.3));
    colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.95 });
  return new THREE.Mesh(geo, mat);
}

/* 草叶实例：小四角锥沿法线站立，随机高度/倾斜/绿色相。
 * exclude: [{ dir: Vector3(单位), angle: 角距弧度 }] */
function makeGrass(radius, count, seed, exclude = []) {
  const bladeGeo = new THREE.ConeGeometry(0.028, 1, 3);
  bladeGeo.translate(0, 0.5, 0);
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.9, flatShading: true });
  const mesh = new THREE.InstancedMesh(bladeGeo, mat, count);
  const rnd = mulberry32(seed);
  const dummy = new THREE.Object3D();
  const greenA = new THREE.Color(0x4f9e3a);
  const greenB = new THREE.Color(0x8fc957);
  const col = new THREE.Color();
  const tilt = new THREE.Quaternion();
  let placed = 0; let guard = 0;
  while (placed < count && guard < count * 12) {
    guard++;
    const z = rnd() * 2 - 1;
    const a = rnd() * Math.PI * 2;
    const rxy = Math.sqrt(1 - z * z);
    const dir = new THREE.Vector3(rxy * Math.cos(a), z, rxy * Math.sin(a));
    if (isExcluded(dir, exclude)) continue;
    const h = 0.12 + rnd() * 0.16;
    dummy.position.copy(dir).multiplyScalar(radius + 0.01);
    dummy.quaternion.setFromUnitVectors(UP_Y, dir);
    tilt.setFromEuler(new THREE.Euler((rnd() - 0.5) * 0.5, 0, (rnd() - 0.5) * 0.5));
    dummy.quaternion.multiply(tilt);
    dummy.scale.set(0.7 + rnd() * 0.6, h, 0.7 + rnd() * 0.6);
    dummy.updateMatrix();
    mesh.setMatrixAt(placed, dummy.matrix);
    col.copy(greenA).lerp(greenB, rnd());
    mesh.setColorAt(placed, col);
    placed++;
  }
  mesh.count = placed;
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  return mesh;
}

function latLonToDirVec(latDeg, lonDeg) {
  const d = latLonToDir(latDeg, lonDeg);
  return new THREE.Vector3(d.x, d.y, d.z);
}

/* 小花实例：彩色小球点缀草地。exclude 同 makeGrass */
function makeFlowers(radius, count, seed, exclude = []) {
  const geo = new THREE.SphereGeometry(0.07, 7, 6);
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.7 });
  const mesh = new THREE.InstancedMesh(geo, mat, count);
  const rnd = mulberry32(seed + 7);
  const dummy = new THREE.Object3D();
  const palette = [0xe85d6a, 0xf5d14a, 0xffffff, 0xb98ae0].map(h => new THREE.Color(h));
  let placed = 0; let guard = 0;
  while (placed < count && guard < count * 14) {
    guard++;
    const z = rnd() * 2 - 1;
    const a = rnd() * Math.PI * 2;
    const rxy = Math.sqrt(1 - z * z);
    const dir = new THREE.Vector3(rxy * Math.cos(a), z, rxy * Math.sin(a));
    if (isExcluded(dir, exclude)) continue;
    dummy.position.copy(dir).multiplyScalar(radius + 0.06);
    dummy.scale.setScalar(0.7 + rnd() * 0.8);
    dummy.updateMatrix();
    mesh.setMatrixAt(placed, dummy.matrix);
    mesh.setColorAt(placed, palette[Math.floor(rnd() * palette.length)]);
    placed++;
  }
  mesh.count = placed;
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  return mesh;
}

function makeLabel(text) {
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 80;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(30,28,24,0.55)';
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(8, 12, 240, 56, 28); else ctx.rect(8, 12, 240, 56);
  ctx.fill();
  ctx.font = '34px Georgia, "SimSun", serif';
  ctx.fillStyle = '#ffeec8';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 128, 41);
  const tex = new THREE.CanvasTexture(canvas);
  const spr = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
  spr.scale.set(1.7, 0.53, 1);
  return spr;
}

/* 金色出发台：地上光环 + 旋转光柱 */
function makeLaunchPad() {
  const g = new THREE.Group();
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.95, 0.06, 8, 40),
    new THREE.MeshStandardMaterial({ color: 0xf2c548, emissive: 0xb8831e, emissiveIntensity: 1.1, roughness: 0.4 })
  );
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.05;
  g.add(ring);
  const beam = new THREE.Mesh(
    new THREE.CylinderGeometry(0.26, 0.46, 4.2, 20, 1, true),
    new THREE.MeshBasicMaterial({
      color: 0xffd27a, transparent: true, opacity: 0.12,
      side: THREE.DoubleSide, depthWrite: false,
    })
  );
  beam.position.y = 2.1;
  beam.name = 'padBeam';
  g.add(beam);
  const light = new THREE.PointLight(0xffcf7a, 5, 12);
  light.position.y = 1.4;
  g.add(light);
  return g;
}

function makeRoseDome() {
  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(0.75, 20, 14, 0, Math.PI * 2, 0, Math.PI / 2),
    new THREE.MeshPhongMaterial({ color: 0xdff2ff, transparent: true, opacity: 0.25, shininess: 120, side: THREE.DoubleSide })
  );
  dome.position.y = 0.05;
  return dome;
}

function makeBaobab() {
  const g = new THREE.Group();
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.16, 0.34, 1.5, 7),
    new THREE.MeshStandardMaterial({ color: 0x7a5a3a, roughness: 0.9 })
  );
  trunk.position.y = 0.75;
  g.add(trunk);
  const leafMat = new THREE.MeshStandardMaterial({ color: 0x3f8a4f, roughness: 0.85, flatShading: true });
  for (let i = 0; i < 4; i++) {
    const leaf = new THREE.Mesh(new THREE.ConeGeometry(0.45, 0.9, 6), leafMat);
    const a = (i / 4) * Math.PI * 2 + 0.4;
    leaf.position.set(Math.cos(a) * 0.3, 1.7, Math.sin(a) * 0.3);
    leaf.rotation.z = Math.cos(a) * 0.35;
    leaf.rotation.x = Math.sin(a) * 0.35;
    g.add(leaf);
  }
  return g;
}

function makeRock(scaleF = 1) {
  return new THREE.Mesh(
    new THREE.DodecahedronGeometry(0.3 * scaleF, 0),
    new THREE.MeshStandardMaterial({ color: 0xa89a86, roughness: 1, flatShading: true })
  );
}

function makeCactus(scaleF = 1) {
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: 0x4f8f52, roughness: 0.9, flatShading: true });
  const trunk = new THREE.Mesh(new THREE.CapsuleGeometry(0.14, 0.7, 4, 8), mat);
  trunk.position.y = 0.55 * scaleF;
  g.add(trunk);
  for (const s of [-1, 1]) {
    const arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.32, 4, 8), mat);
    arm.position.set(s * 0.24 * scaleF, 0.62 * scaleF, 0);
    arm.rotation.z = -s * 0.7;
    g.add(arm);
  }
  g.scale.setScalar(scaleF);
  return g;
}

/* 金色麦田：环绕狐狸的一片麦穗（地球专属，对应"麦田本来与我无关"） */
function makeWheat(radius, centerLat, centerLon) {
  const COUNT = 70;
  const geo = new THREE.ConeGeometry(0.045, 1, 4);
  geo.translate(0, 0.5, 0);
  const mat = new THREE.MeshStandardMaterial({ color: 0xd9b44a, roughness: 0.9, flatShading: true });
  const mesh = new THREE.InstancedMesh(geo, mat, COUNT);
  const center = latLonToDirVec(centerLat, centerLon);
  const north = new THREE.Vector3(0, 1, 0).addScaledVector(center, -center.y).normalize();
  const east = new THREE.Vector3().crossVectors(center, north).normalize();
  const rnd = mulberry32(7701);
  const dummy = new THREE.Object3D();
  const tilt = new THREE.Quaternion();
  let placed = 0;
  while (placed < COUNT) {
    // 切平面高斯散布 → 投回球面方向
    const a = rnd() * Math.PI * 2;
    const r = Math.pow(rnd(), 0.6) * 2.0;
    const dir = center.clone()
      .addScaledVector(north, Math.cos(a) * r / radius)
      .addScaledVector(east, Math.sin(a) * r / radius).normalize();
    if (dir.angleTo(center) < 0.11) continue; // 狐狸脚下留空
    const h = 0.32 + rnd() * 0.26;
    dummy.position.copy(dir).multiplyScalar(radius + 0.01);
    dummy.quaternion.setFromUnitVectors(UP_Y, dir);
    tilt.setFromEuler(new THREE.Euler((rnd() - 0.5) * 0.35, 0, (rnd() - 0.5) * 0.35));
    dummy.quaternion.multiply(tilt);
    dummy.scale.set(0.8 + rnd() * 0.5, h, 0.8 + rnd() * 0.5);
    dummy.updateMatrix();
    mesh.setMatrixAt(placed++, dummy.matrix);
  }
  mesh.instanceMatrix.needsUpdate = true;
  return mesh;
}

function makeStars() {
  const COUNT = 1600;
  const positions = new Float32Array(COUNT * 3);
  const colors = new Float32Array(COUNT * 3);
  const white = new THREE.Color(0xf5f6ff);
  const gold = new THREE.Color(0xffd98a);
  const c = new THREE.Color();
  const rnd = mulberry32(20261022);
  for (let i = 0; i < COUNT; i++) {
    let x, y, z, l;
    do { x = rnd() * 2 - 1; y = rnd() * 2 - 1; z = rnd() * 2 - 1; l = x * x + y * y + z * z; } while (l > 1 || l < 1e-4);
    const r = 380 + rnd() * 520;
    const inv = r / Math.sqrt(l);
    positions[i * 3] = x * inv; positions[i * 3 + 1] = y * inv; positions[i * 3 + 2] = z * inv;
    c.copy(white).lerp(gold, rnd() * 0.5);
    colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return new THREE.Points(geo, new THREE.PointsMaterial({
    size: 1.6, vertexColors: true, sizeAttenuation: true,
    transparent: true, opacity: 0.55, fog: false,
  }));
}

/* 采样点是否落在排除锥内（NPC/道具周围不长草/不落石） */
function isExcluded(dirVec, excludeDirs) {
  return excludeDirs.some(({ dir, angle }) => dirVec.angleTo(dir) < angle);
}

function buildDecor(def, group) {
  const R = def.radius;
  const rnd = mulberry32(def.id.length * 999 + 7);
  // NPC/道具周围的草排除区（角距按角色身高/球半径缩放）
  const exclude = def.npcs.map(n => ({
    dir: latLonToDirVec(n.lat, n.lon),
    angle: Math.max(0.18, n.height / R * 0.9),
  }));
  // 出发台也留空
  exclude.push({ dir: latLonToDirVec(def.pad.lat, def.pad.lon), angle: 0.35 });
  // 混元道具周围同样留空
  for (const p of def.props ?? []) {
    exclude.push({ dir: latLonToDirVec(p.lat, p.lon), angle: Math.max(0.22, (p.height ?? 1) / R * 0.7) });
  }

  if (def.grass) group.add(makeGrass(R, def.grass, def.id.length * 131 + 3, exclude));
  if (def.flowers) group.add(makeFlowers(R, def.flowers, def.id.length * 211 + 9, exclude));

  const rockCount = def.id === 'b612' ? 14 : 6;
  let placed = 0; let guard = 0;
  while (placed < rockCount && guard < rockCount * 12) {
    guard++;
    const la = rnd() * 150 - 75;
    const lo = rnd() * 360;
    const d = latLonToDirVec(la, lo);
    if (isExcluded(d, exclude)) continue;
    const rock = makeRock(0.6 + rnd() * 1.1);
    rock.position.y = 0.16;
    rock.rotation.y = rnd() * Math.PI * 2;
    const wrap = new THREE.Group();
    wrap.add(rock);
    group.add(placeOnSphere(wrap, R, la, lo, 0.03));
    placed++;
  }

  if (def.id === 'b612') {
    // 活/死火山与大猴面包树均已换成混元 GLB（见 def.props），这里只留两棵程序化小树
    group.add(placeOnSphere(makeBaobab(), R, -30, 200, 0.05));
    group.add(placeOnSphere(makeBaobab(), R, 60, 300, 0.05));
  }
  if (def.id === 'earth') {
    for (const [la, lo, s] of [[20, 40, 1.1], [-26, -40, 0.9], [34, -90, 1.3], [-4, 70, 0.8]]) {
      group.add(placeOnSphere(makeCactus(s), R, la, lo, 0.04));
    }
    if (def.wheat) group.add(makeWheat(R, def.wheat.lat, def.wheat.lon));
  }
}

/* 混元道具（无名字牌）：只建静态锚点，GLB 由 enterWorld 按需加载。
 * face='spawn' 时面向出生点，glow 时在道具上方加点光（光属静态层） */
function buildPropAnchors(def, group, slots) {
  for (const p of def.props ?? []) {
    const sink = p.sink ?? 0.02;
    const anchor = p.face
      ? makeFacingAnchor(def.radius, p.lat, p.lon, p.face === 'spawn' ? def.spawn : p.face, sink)
      : placeOnSphere(new THREE.Group(), def.radius, p.lat, p.lon, sink);
    anchor.name = `prop:${p.model.split('/').pop()}`;
    if (p.glow) {
      const light = new THREE.PointLight(p.glow, 5, 9);
      light.position.y = p.height * 0.75;
      anchor.add(light);
    }
    group.add(anchor);
    slots.push({ anchor, model: p.model, height: p.height, yaw: p.yaw ?? 0, wrap: null });
  }
}

/* GLB 异步到位后的弹入动画（main 循环每帧 tickReveals） */
const revealAnims = [];
function startReveal(obj, dur = 0.45) {
  obj.scale.setScalar(0.55);
  revealAnims.push({ obj, t: 0, dur });
}
export function tickReveals(dt) {
  for (let i = revealAnims.length - 1; i >= 0; i--) {
    const r = revealAnims[i];
    if (!r.obj.parent) { // 已被 exitWorld 卸载
      revealAnims.splice(i, 1);
      continue;
    }
    r.t += dt;
    const k = Math.min(r.t / r.dur, 1);
    const e = 1 - Math.pow(1 - k, 3); // ease-out cubic
    r.obj.scale.setScalar(0.55 + 0.45 * e);
    if (k >= 1) revealAnims.splice(i, 1);
  }
}

/* 释放一棵 GLB 子树的 GPU 资源（Set 去重：MR 贴图同挂 metalness/roughness 两槽） */
function disposeObject(root) {
  const geos = new Set();
  const mats = new Set();
  root.traverse((o) => {
    if (o.geometry) geos.add(o.geometry);
    if (Array.isArray(o.material)) o.material.forEach((m) => mats.add(m));
    else if (o.material) mats.add(o.material);
  });
  const texs = new Set();
  for (const mat of mats) {
    for (const key in mat) {
      const v = mat[key];
      if (v && v.isTexture) texs.add(v);
    }
  }
  geos.forEach((g) => g.dispose());
  texs.forEach((t) => t.dispose());
  mats.forEach((m) => m.dispose());
}

/* 进入星球：按需拉取该星 NPC/道具 GLB。
 * gen 作废在途请求（快速横跳时旧结果到达即 dispose，绝不挂载/泄漏）。
 * 静态层（地面/草/出发台/名字牌/锚点）启动时已建好且全程保留——
 * 远景悬浮的小行星与光柱本来就是旅行时的可见景观。 */
export function enterWorld(world) {
  world.gen += 1;
  const gen = world.gen;
  const jobs = world.slots.map(async (slot) => {
    let gltf;
    try {
      gltf = await gltfLoader.loadAsync(assetPath(slot.model));
    } catch (e) {
      if (gen === world.gen) console.warn(`${slot.model} 加载失败`, e);
      return; // 锚点/名字牌仍在，不黑屏不抛
    }
    if (gen !== world.gen) {
      disposeObject(gltf.scene); // 迟到的回复：世界已离开，立即释放
      return;
    }
    const wrap = normalizeProp(gltf.scene, slot.height, slot.yaw);
    slot.anchor.add(wrap);
    slot.wrap = wrap;
    startReveal(wrap);
  });
  world.loadReady = Promise.allSettled(jobs).then(() => {}); // 恒 resolve，防止黑屏死等
  return world.loadReady;
}

/* 离开星球：卸载全部 GLB wrap，静态层保留 */
export function exitWorld(world) {
  world.gen += 1; // 在途 loadAsync 的回调到达时一律走"迟到"分支
  for (const slot of world.slots) {
    if (!slot.wrap) continue;
    slot.wrap.removeFromParent();
    disposeObject(slot.wrap);
    slot.wrap = null;
  }
  for (let i = revealAnims.length - 1; i >= 0; i--) {
    if (!revealAnims[i].obj.parent) revealAnims.splice(i, 1);
  }
}

function buildWorld(scene, def) {
  const group = new THREE.Group();
  group.position.fromArray(def.center);
  const ground = makeGround(def.radius, def.palette);
  ground.userData.isGround = true; // 右键点地 raycast 的命中目标
  group.add(ground);
  buildDecor(def, group);

  // 动态层槽位：锚点/灯光/名字牌属静态层（启动即建、常驻），
  // GLB wrap 由 enterWorld/exitWorld 按需挂载与释放
  const slots = [];
  buildPropAnchors(def, group, slots);

  // NPC 锚点 + 名字牌，一律面向本星出生点（玩家来路）
  const npcRuntimes = [];
  for (const npc of def.npcs) {
    const anchor = makeFacingAnchor(def.radius, npc.lat, npc.lon, def.spawn);
    anchor.name = `npc:${npc.model.split('/').pop()}`;
    if (npc.dome) anchor.add(makeRoseDome());
    const label = makeLabel(npc.label);
    label.position.y = npc.height + 0.55;
    anchor.add(label);
    group.add(anchor);
    npcRuntimes.push({ key: npc.dialogue, label: npc.label, anchor });
    slots.push({ anchor, model: npc.model, height: npc.height, yaw: npc.yaw, wrap: null });
  }

  // 出发台
  const pad = makeLaunchPad();
  placeOnSphere(pad, def.radius, def.pad.lat, def.pad.lon, 0.02);
  group.add(pad);

  scene.add(group);
  const center = new THREE.Vector3().fromArray(def.center);
  return {
    def, group,
    center,
    ground,
    npcs: npcRuntimes,
    slots,
    gen: 0,
    loadReady: Promise.resolve(),
    padLocal: dirToLocal(def.radius, def.pad.lat, def.pad.lon),
    padWorld: center.clone().add(dirToLocal(def.radius, def.pad.lat, def.pad.lon)),
  };
}

export function createWorlds(scene) {
  scene.background = new THREE.Color(0x8fc6ee);
  scene.fog = new THREE.Fog(0x9fcdf2, 460, 1200);

  scene.add(makeStars());

  // 远处再放一颗带环行星做装饰
  const ringed = new THREE.Mesh(
    new THREE.SphereGeometry(20, 24, 18),
    new THREE.MeshStandardMaterial({ color: 0x7fa8c9, roughness: 0.85, flatShading: true, fog: false })
  );
  ringed.position.set(-320, 150, -380);
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(30, 3, 2, 48),
    new THREE.MeshStandardMaterial({ color: 0xd9c9a0, roughness: 0.7, side: THREE.DoubleSide, fog: false })
  );
  ring.rotation.x = Math.PI / 2.4;
  ringed.add(ring);
  scene.add(ringed);

  const worlds = WORLD_DEFS.map(d => buildWorld(scene, d));
  const map = new Map(worlds.map(w => [w.def.id, w]));

  // 白昼光照：暖阳主光 + 天空环境光
  const sun = new THREE.DirectionalLight(0xfff4dd, 2.8);
  sun.position.set(-160, 90, -260).normalize().multiplyScalar(100);
  scene.add(sun);
  scene.add(new THREE.AmbientLight(0x9fc0e8, 1.05));
  scene.add(new THREE.HemisphereLight(0xcdeaff, 0x86a066, 0.9));

  return { list: worlds, byId: map, b612: map.get('b612') };
}
