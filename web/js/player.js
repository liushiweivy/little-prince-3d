/* 小王子角色：TripoSR GLB（M1，加载完成前用几何体占位），球面重力移动 + 跳跃 */
import * as THREE from '../vendor/three.module.min.js';
import { GLTFLoader } from '../vendor/loaders/GLTFLoader.js';
import { moveOnSphere, latLonToDir } from './sphere-math.js';

const WALK_SPEED = 4;
const RUN_MULT = 1.8;
const GRAVITY = 22;
const JUMP_VEL = 7.5;

const MODEL_URL = './models/little-prince.glb';
const MODEL_HEIGHT = 1.1;   // 比例约定：角色高 1.1 单位
const MODEL_YAW = Math.PI / 2; // GLB 原始朝向 -X，转到本地 +Z（与占位几何体一致）

function buildPrince() {
  const g = new THREE.Group();
  const skin = new THREE.MeshStandardMaterial({ color: 0xf2d3b3, roughness: 0.7 });
  const suit = new THREE.MeshStandardMaterial({ color: 0x3f7d5a, roughness: 0.75 });
  const hairMat = new THREE.MeshStandardMaterial({ color: 0xf5c94a, roughness: 0.6 });
  const scarfMat = new THREE.MeshStandardMaterial({ color: 0xd94f3d, roughness: 0.65 });

  // 身体（绿色套装）
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.26, 0.42, 4, 10), suit);
  body.position.y = 0.55;
  g.add(body);
  // 头
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.26, 16, 12), skin);
  head.position.y = 1.12;
  g.add(head);
  // 金发（略大的半球，向后上方偏移）
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.28, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.55), hairMat);
  hair.position.set(0, 1.16, -0.04);
  hair.rotation.x = -0.25;
  g.add(hair);
  // 眼睛
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0x1a1a22 });
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.035, 6, 6), eyeMat);
    eye.position.set(s * 0.09, 1.14, 0.235);
    g.add(eye);
  }
  // 围巾：颈圈 + 身后飘带
  const collar = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.055, 8, 16), scarfMat);
  collar.position.y = 0.92;
  collar.rotation.x = Math.PI / 2;
  g.add(collar);
  const tail = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.5, 0.03), scarfMat);
  tail.position.set(0, 0.72, -0.3);
  tail.rotation.x = 0.5;
  g.add(tail);

  g.traverse((o) => { if (o.isMesh) { o.castShadow = false; } });
  return g;
}

/* GLB 归一化：XZ 居中、脚底贴 y=0、身高缩放到 MODEL_HEIGHT、朝向本地 +Z */
function normalizeModel(obj) {
  const box = new THREE.Box3().setFromObject(obj);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const s = MODEL_HEIGHT / size.y;
  const wrap = new THREE.Group();
  obj.position.set(-center.x * s, -box.min.y * s, -center.z * s);
  obj.scale.setScalar(s);
  obj.rotation.y = MODEL_YAW;
  wrap.add(obj);
  return wrap;
}

export class Player {
  constructor(scene, radius, spawnLat = 0, spawnLon = 0) {
    this.radius = radius;
    const dir = latLonToDir(spawnLat, spawnLon);
    this.pos = new THREE.Vector3(dir.x, dir.y, dir.z).multiplyScalar(radius);
    this.forward = new THREE.Vector3(0, 0, 1); // 切向朝向，首帧会投影到切平面
    this.height = 0;   // 离地高度（沿 up 方向）
    this.vSpeed = 0;   // 竖直（径向）速度
    this.mesh = buildPrince(); // 占位，GLB 就绪后替换
    scene.add(this.mesh);
    new GLTFLoader().load(MODEL_URL, (gltf) => {
      const model = normalizeModel(gltf.scene);
      this.mesh.clear();
      this.mesh.add(model);
    }, undefined, (e) => {
      console.warn('little-prince.glb 加载失败，保留占位几何体', e);
    });
    this.syncMesh();
  }

  get up() {
    return this.pos.clone().normalize();
  }

  /* moveDir：相机相对切向单位向量（已合成 WASD）；jump：本帧是否按跳；running：是否加速 */
  update(dt, moveDir, jump, running) {
    const speed = WALK_SPEED * (running ? RUN_MULT : 1);
    if (moveDir) {
      const step = moveOnSphere(this.pos, moveDir, speed * dt);
      this.pos.set(step.pos.x, step.pos.y, step.pos.z);
      if (Math.hypot(step.forward.x, step.forward.y, step.forward.z) > 1e-6) {
        this.forward.set(step.forward.x, step.forward.y, step.forward.z).normalize();
      }
    }
    // 径向跳跃/重力
    if (jump && this.height === 0) this.vSpeed = JUMP_VEL;
    if (this.height > 0 || this.vSpeed > 0) {
      this.vSpeed -= GRAVITY * dt;
      this.height += this.vSpeed * dt;
      if (this.height <= 0) { this.height = 0; this.vSpeed = 0; }
    }
    this.syncMesh();
  }

  syncMesh() {
    const up = this.up;
    // forward 正交化到当前切平面（跳跃不改变朝向）
    const f = this.forward.clone().addScaledVector(up, -this.forward.dot(up));
    if (f.lengthSq() < 1e-10) f.set(0, 0, 1).addScaledVector(up, -up.z);
    f.normalize();
    this.forward.copy(f);

    const xAxis = new THREE.Vector3().crossVectors(up, f); // 右 = up × forward
    const m = new THREE.Matrix4().makeBasis(xAxis, up, f);
    this.mesh.quaternion.setFromRotationMatrix(m);
    this.mesh.position.copy(up).multiplyScalar(this.radius + this.height);
  }
}
