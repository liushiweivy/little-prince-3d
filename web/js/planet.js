/* 星球与场景：B612 地面、玫瑰（玻璃罩）、猴面包树、火山、星空与远处行星 */
import * as THREE from '../vendor/three.module.min.js';
import { latLonToDir } from './sphere-math.js';

export const PLANET_RADIUS = 10;

const UP_Y = new THREE.Vector3(0, 1, 0);

/* 把道具放到球面 lat/lon 处，Y 轴对齐法线；sink>0 时往地里沉一点 */
function placeOnSphere(obj, latDeg, lonDeg, sink = 0) {
  const dir = latLonToDir(latDeg, lonDeg);
  const p = new THREE.Vector3(dir.x, dir.y, dir.z).multiplyScalar(PLANET_RADIUS - sink);
  obj.position.copy(p);
  obj.quaternion.setFromUnitVectors(UP_Y, p.clone().normalize());
  return obj;
}

function makeGround() {
  const geo = new THREE.IcosahedronGeometry(PLANET_RADIUS, 6);
  const posAttr = geo.getAttribute('position');
  const colors = new Float32Array(posAttr.count * 3);
  const base = new THREE.Color(0x8e7fb8); // 薰衣草灰
  const dark = new THREE.Color(0x6a5f92);
  const gold = new THREE.Color(0xb8a06a); // 鎏金斑块
  const c = new THREE.Color();
  for (let i = 0; i < posAttr.count; i++) {
    const x = posAttr.getX(i), y = posAttr.getY(i), z = posAttr.getZ(i);
    const n = Math.sin(x * 1.7) * Math.cos(z * 1.3) + Math.sin(y * 2.1 + x);
    c.copy(base).lerp(n > 0 ? dark : gold, Math.min(0.45, Math.abs(n) * 0.3));
    colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.95 });
  return new THREE.Mesh(geo, mat);
}

function makeRose() {
  const g = new THREE.Group();
  const green = new THREE.MeshStandardMaterial({ color: 0x3f8f5a, roughness: 0.8 });
  const red = new THREE.MeshStandardMaterial({ color: 0xc23a4e, roughness: 0.6 });
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.045, 0.9, 6), green);
  stem.position.y = 0.45;
  g.add(stem);
  for (let i = 0; i < 6; i++) {
    const petal = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.3, 5), red);
    const a = (i / 6) * Math.PI * 2;
    petal.position.set(Math.cos(a) * 0.12, 1.0, Math.sin(a) * 0.12);
    petal.rotation.set(Math.PI * 0.32, 0, -a);
    g.add(petal);
  }
  const core = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 6), red);
  core.position.y = 1.02;
  g.add(core);
  // 玻璃罩：小王子给玫瑰罩的那个
  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(0.75, 20, 14, 0, Math.PI * 2, 0, Math.PI / 2),
    new THREE.MeshPhongMaterial({ color: 0xcfe8ff, transparent: true, opacity: 0.22, shininess: 120, side: THREE.DoubleSide })
  );
  dome.position.y = 0.05;
  g.add(dome);
  return g;
}

function makeBaobab() {
  const g = new THREE.Group();
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.16, 0.34, 1.5, 7),
    new THREE.MeshStandardMaterial({ color: 0x7a5a3a, roughness: 0.9 })
  );
  trunk.position.y = 0.75;
  g.add(trunk);
  const leafMat = new THREE.MeshStandardMaterial({ color: 0x2e6b46, roughness: 0.85, flatShading: true });
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

function makeVolcano(active) {
  const g = new THREE.Group();
  const cone = new THREE.Mesh(
    new THREE.CylinderGeometry(0.28, 1.0, 1.2, 9),
    new THREE.MeshStandardMaterial({ color: 0x8a8078, roughness: 1, flatShading: true })
  );
  cone.position.y = 0.6;
  g.add(cone);
  const crater = new THREE.Mesh(
    new THREE.CylinderGeometry(0.24, 0.24, 0.12, 9),
    new THREE.MeshStandardMaterial({
      color: 0x2b2320,
      emissive: active ? 0xff5a1f : 0x000000,
      emissiveIntensity: active ? 0.9 : 0,
    })
  );
  crater.position.y = 1.2;
  g.add(crater);
  if (active) {
    const glow = new THREE.PointLight(0xff7a33, 6, 9);
    glow.position.y = 1.6;
    g.add(glow);
  }
  return g;
}

function makeRock(scaleF = 1) {
  const rock = new THREE.Mesh(
    new THREE.DodecahedronGeometry(0.3 * scaleF, 0),
    new THREE.MeshStandardMaterial({ color: 0x9a93a8, roughness: 1, flatShading: true })
  );
  rock.position.y = 0.16 * scaleF;
  return rock;
}

function makeStars() {
  const COUNT = 1600;
  const positions = new Float32Array(COUNT * 3);
  const colors = new Float32Array(COUNT * 3);
  const white = new THREE.Color(0xf5f2ff);
  const gold = new THREE.Color(0xffd98a);
  const c = new THREE.Color();
  for (let i = 0; i < COUNT; i++) {
    // 均匀球壳随机（Marsaglia 法）
    let x, y, z, l;
    do { x = Math.random() * 2 - 1; y = Math.random() * 2 - 1; z = Math.random() * 2 - 1; l = x * x + y * y + z * z; } while (l > 1 || l < 1e-4);
    const r = 320 + Math.random() * 480;
    const inv = r / Math.sqrt(l);
    positions[i * 3] = x * inv; positions[i * 3 + 1] = y * inv; positions[i * 3 + 2] = z * inv;
    c.copy(white).lerp(gold, Math.random() * 0.5);
    colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return new THREE.Points(geo, new THREE.PointsMaterial({ size: 1.6, vertexColors: true, sizeAttenuation: true }));
}

function makeSkyPlanets() {
  const g = new THREE.Group();
  const orange = new THREE.Mesh(
    new THREE.SphereGeometry(14, 24, 18),
    new THREE.MeshStandardMaterial({ color: 0xd98e4a, emissive: 0x5a2e10, roughness: 0.9, flatShading: true })
  );
  orange.position.set(-160, 90, -260);
  g.add(orange);
  // 带环行星：致敬 B612 的邻居们
  const ringed = new THREE.Mesh(
    new THREE.SphereGeometry(9, 24, 18),
    new THREE.MeshStandardMaterial({ color: 0x7fa8c9, emissive: 0x1c2f44, roughness: 0.85, flatShading: true })
  );
  ringed.position.set(210, -60, -180);
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(14, 1.6, 2, 48),
    new THREE.MeshStandardMaterial({ color: 0xd9c9a0, roughness: 0.7, side: THREE.DoubleSide })
  );
  ring.rotation.x = Math.PI / 2.4;
  ringed.add(ring);
  g.add(ringed);
  return g;
}

export function createPlanet(scene) {
  scene.background = new THREE.Color(0x0a0e1f);

  scene.add(makeGround());
  scene.add(makeStars());
  scene.add(makeSkyPlanets());

  placeOnSphere(makeRose(), 8, 10, 0.02);
  scene.add(placeOnSphere(makeBaobab(), 40, 120, 0.05));
  scene.add(placeOnSphere(makeBaobab(), -30, 200, 0.05));
  scene.add(placeOnSphere(makeBaobab(), 60, 300, 0.05));
  scene.add(placeOnSphere(makeVolcano(true), -45, 60, 0.1));
  scene.add(placeOnSphere(makeVolcano(false), -52, 75, 0.1));
  for (let i = 0; i < 14; i++) {
    const rock = makeRock(0.6 + Math.random() * 1.3);
    rock.rotation.y = Math.random() * Math.PI * 2;
    const g = new THREE.Group();
    g.add(rock);
    scene.add(placeOnSphere(g, Math.random() * 160 - 80, Math.random() * 360, 0.03));
  }

  // 光照：暖阳主光 + 冷环境补光，深夜靛蓝氛围
  const sun = new THREE.DirectionalLight(0xffe3b3, 2.4);
  sun.position.set(-160, 90, -260).normalize().multiplyScalar(100);
  scene.add(sun);
  scene.add(new THREE.AmbientLight(0x4a5878, 1.6));
  const hemi = new THREE.HemisphereLight(0x8a9fd9, 0x3a3450, 1.0);
  scene.add(hemi);
}
