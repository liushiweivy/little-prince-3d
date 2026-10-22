/* 小王子角色：混元3D GLB（M1，加载完成前用几何体小人占位），球面重力移动 + 跳跃。
 * 静态模型没有骨骼动作，用程序化运动学缓解"僵尸滑步"：
 * 走路起伏/前倾/重心左右转移、转向平滑、起跳拉伸、落地挤压、待机呼吸。
 * 若将来接入带 AnimationMixer 的绑骨模型（prince_rigged.glb），程序步态自动让位。 */
import * as THREE from '../vendor/three.module.min.js';
import { GLTFLoader } from '../vendor/loaders/GLTFLoader.js';
import { moveOnSphere, latLonToDir } from './sphere-math.js';
import { assetPath } from './assets.js';

const WALK_SPEED = 4;
const RUN_MULT = 1.8;
const GRAVITY = 22;
const JUMP_VEL = 7.5;
const TURN_RATE = 13;        // 朝向指数跟随速率（rad/s 量级）
const JUMP_STRETCH = 0.14;   // 起跳动画时长（秒）
const LAND_SQUASH = 0.2;     // 落地动画时长（秒）

// 角色模型：rigged = Mixamo 绑骨带动画版（默认，缺文件时回退静态混元）；
// ?model=hunyuan/hunyuan100k/triposr 可看旧的静态模型
const MODEL_VARIANTS = {
  rigged: { file: './models/prince_rigged.glb', yaw: 0, animated: true }, // Mixamo 绑骨 idle/walk/run
  hunyuan: { file: './models/hunyuan-prince.glb', yaw: 0 },        // 混元 Pro 50 万面 master（28MB）
  hunyuan100k: { file: './models/hunyuan-prince-100k.glb', yaw: 0 }, // 混元 Pro 10 万面轻量版（14MB）
  triposr: { file: './models/little-prince.glb', yaw: Math.PI / 2 },
};
// TODO: AccuRIG 绑骨产出 prince_rigged.glb 后，默认切回 'rigged'
const qsModel = new URLSearchParams(location.search).get('model');
const MODEL_VARIANT = MODEL_VARIANTS[qsModel] ? qsModel : 'hunyuan';
const { file: MODEL_FILE, yaw: MODEL_YAW, animated: MODEL_ANIMATED } = MODEL_VARIANTS[MODEL_VARIANT];
const MODEL_URL = assetPath(MODEL_FILE);
// 绑骨版没产出时回退；回退路径同样过 lite 开关，避免回退即拉 14MB 原档
const MODEL_FALLBACK = { ...MODEL_VARIANTS.hunyuan100k, file: assetPath(MODEL_VARIANTS.hunyuan100k.file) };
const MODEL_HEIGHT = 1.1;   // 比例约定：角色高 1.1 单位

// 动作在 timeScale=1 时对应的切平面位移速度（m/s），用于按实际速度缩放周期防滑步
const ANIM_GROUND_SPEED = { idle: 0, walk: 2.0, run: 3.6 };

/* 加载占位：可辨认的小人（绿套装、金发、红围巾、佩剑），不再是"一个球" */
function buildPrince() {
  const g = new THREE.Group();
  const skin = new THREE.MeshStandardMaterial({ color: 0xf2d3b3, roughness: 0.7 });
  const suit = new THREE.MeshStandardMaterial({ color: 0x3f7d5a, roughness: 0.75 });
  const pants = new THREE.MeshStandardMaterial({ color: 0x35664c, roughness: 0.8 });
  const hairMat = new THREE.MeshStandardMaterial({ color: 0xf5c94a, roughness: 0.6 });
  const scarfMat = new THREE.MeshStandardMaterial({ color: 0xd94f3d, roughness: 0.65 });
  const bladeMat = new THREE.MeshStandardMaterial({ color: 0xd8dee6, roughness: 0.3, metalness: 0.7 });

  // 腿 + 脚
  for (const s of [-1, 1]) {
    const leg = new THREE.Mesh(new THREE.CapsuleGeometry(0.085, 0.24, 4, 8), pants);
    leg.position.set(s * 0.11, 0.23, 0);
    g.add(leg);
    const foot = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.07, 0.21), pants);
    foot.position.set(s * 0.11, 0.045, 0.04);
    g.add(foot);
  }
  // 身体（绿色套装）
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.24, 0.32, 4, 10), suit);
  body.position.y = 0.6;
  g.add(body);
  // 手臂
  for (const s of [-1, 1]) {
    const arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.065, 0.28, 4, 8), suit);
    arm.position.set(s * 0.28, 0.62, 0.02);
    arm.rotation.z = -s * 0.12;
    g.add(arm);
  }
  // 头
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.24, 16, 12), skin);
  head.position.y = 1.06;
  g.add(head);
  // 金发（略大的半球，向后上方偏移）
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.26, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.55), hairMat);
  hair.position.set(0, 1.1, -0.04);
  hair.rotation.x = -0.25;
  g.add(hair);
  // 眼睛
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0x1a1a22 });
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.033, 6, 6), eyeMat);
    eye.position.set(s * 0.085, 1.08, 0.22);
    g.add(eye);
  }
  // 围巾：颈圈 + 身后飘带（飘带会随步态摆动）
  const collar = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.052, 8, 16), scarfMat);
  collar.position.y = 0.87;
  collar.rotation.x = Math.PI / 2;
  g.add(collar);
  const tail = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.46, 0.03), scarfMat);
  tail.position.set(0, 0.67, -0.28);
  tail.rotation.x = 0.5;
  g.add(tail);
  // 佩剑
  const blade = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.3, 0.025), bladeMat);
  blade.position.set(0.27, 0.36, 0.12);
  blade.rotation.z = 0.35;
  g.add(blade);
  const guard = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.025, 0.03), bladeMat);
  guard.position.set(0.22, 0.47, 0.12);
  guard.rotation.z = 0.35;
  g.add(guard);

  g.traverse((o) => { if (o.isMesh) { o.castShadow = false; } });
  return { group: g, tail };
}

/* GLB 归一化：先偏航再量盒（否则非对称模型会被居中偏移带离锚点）、
 * XZ 居中、脚底贴 y=0、身高缩放到 MODEL_HEIGHT */
function normalizeModel(obj, yaw = MODEL_YAW) {
  obj.rotation.y = yaw;
  const box = new THREE.Box3().setFromObject(obj);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const s = MODEL_HEIGHT / size.y;
  const wrap = new THREE.Group();
  obj.position.set(-center.x * s, -box.min.y * s, -center.z * s);
  obj.scale.setScalar(s);
  wrap.add(obj);
  return wrap;
}

export class Player {
  /**
   * @param {THREE.Scene} scene
   * @param {{ center: THREE.Vector3, radius: number, spawn: {lat:number, lon:number, face?:{lat:number,lon:number}} }} world
   */
  constructor(scene, world) {
    this.center = world.center.clone();
    this.radius = world.radius;
    const dir = latLonToDir(world.spawn.lat, world.spawn.lon);
    this.pos = new THREE.Vector3(dir.x, dir.y, dir.z).multiplyScalar(this.radius);
    this.forward = new THREE.Vector3(0, 0, 1); // 切向朝向，首帧会投影到切平面
    if (world.spawn.face) this.faceToward(world.spawn.face);
    this.height = 0;   // 离地高度（沿 up 方向）
    this.vSpeed = 0;   // 竖直（径向）速度
    this.speedNow = 0;

    // 层级：mesh（球面目标准向）→ visual（程序步态）→ placeholder / modelRoot（GLB 弹入）
    this.mesh = new THREE.Group();
    this.visual = new THREE.Group();
    this.mesh.add(this.visual);
    const placeholder = buildPrince();
    this.placeholder = placeholder.group;
    this.tail = placeholder.tail;
    this.visual.add(this.placeholder);
    this.modelRoot = new THREE.Group();
    this.visual.add(this.modelRoot);
    scene.add(this.mesh);

    // 步态状态
    this.walkPhase = 0;
    this.idleT = Math.random() * 10;
    this.jumpT = 0;
    this.landT = 0;
    this.modelReveal = 1; // 1 = 无需弹入

    this.mixer = null;
    this.actions = {};
    this.animState = 'idle';
    this.loadModel(MODEL_URL, MODEL_ANIMATED, MODEL_FALLBACK);
    this.syncMesh();
  }

  /* 让朝向指向球面另一经纬度点（取大圆切向），供出生点/传送使用 */
  faceToward(latLon) {
    const spawnN = this.pos.clone().normalize();
    const d = latLonToDir(latLon.lat, latLon.lon);
    const target = new THREE.Vector3(d.x, d.y, d.z);
    const f = target.addScaledVector(spawnN, -target.dot(spawnN));
    if (f.lengthSq() > 1e-10) this.forward.copy(f.normalize());
  }

  /* 切换到另一个星球：换球心/半径，落到 spawn 径向 height 处（过场动画从高处落下） */
  travelTo(world, height = 0) {
    this.center.copy(world.center);
    this.radius = world.radius;
    const dir = latLonToDir(world.spawn.lat, world.spawn.lon);
    this.pos.set(dir.x, dir.y, dir.z).multiplyScalar(this.radius);
    this.forward.set(0, 0, 1);
    if (world.spawn.face) this.faceToward(world.spawn.face);
    this.vSpeed = 0;
    this.height = height;
    this.jumpT = 0;
    this.landT = 0;
    this.syncMesh();
  }

  /* 过场期间只播待机动画并同步模型，不走移动/重力 */
  tickTravel(dt, height) {
    this.height = height;
    this.vSpeed = 0; // 对话/星图把高度钉在 0，残留的跳跃速度不能留到恢复玩法后
    this.speedNow = 0;
    this.updateLocomotion(dt);
    this.syncMesh(dt);
  }

  /* 世界坐标（球心 + 本地径向位置） */
  get worldPos() {
    return this.center.clone().add(this.pos.clone().normalize().multiplyScalar(this.radius + this.height));
  }

  /* 加载角色 GLB；animated=true 时建立 AnimationMixer，失败回退静态模型 */
  loadModel(url, animated, fallback, yaw = MODEL_YAW) {
    new GLTFLoader().load(url, (gltf) => {
      const model = normalizeModel(gltf.scene, yaw);
      this.modelRoot.clear();
      this.modelRoot.add(model);
      this.modelReveal = 0; // 弹入 0.6 → 1
      this.placeholder.visible = false;
      if (animated) {
        this.setupMixer(gltf);
        // 绑骨接管：一次性清掉程序步态在 visual 上的残留（跳/走中途加载完成会冻结拉伸/侧倾）
        this.visual.position.set(0, 0, 0);
        this.visual.rotation.set(0, 0, 0);
        this.visual.scale.set(1, 1, 1);
      }
    }, undefined, (e) => {
      if (fallback) {
        console.warn(`${url} 加载失败，回退 ${fallback.file}`, e);
        this.loadModel(fallback.file, false, null, fallback.yaw ?? MODEL_YAW);
      } else {
        console.warn(`${url} 加载失败，保留占位几何体`, e);
      }
    });
  }

  setupMixer(gltf) {
    this.mixer = new THREE.AnimationMixer(gltf.scene);
    for (const clip of gltf.animations) {
      const name = clip.name.toLowerCase();
      const key = name.startsWith('walk') ? 'walk'
        : name.startsWith('run') ? 'run'
        : name.startsWith('idle') ? 'idle' : name;
      const act = this.mixer.clipAction(clip);
      act.name = key;
      this.actions[key] = act;
    }
    this.actions.idle?.reset().play();
    this.animState = 'idle';
    if (!this.actions.idle) console.warn('GLB 里没有 idle 片段：', gltf.animations.map(c => c.name));
  }

  /* 按切平面速度切换 idle/walk/run，并按速度缩放动作周期（in-place 动画防滑步） */
  updateMixer(dt) {
    if (!this.mixer) return;
    const v = this.speedNow;
    const want = v < 0.6 ? 'idle' : (v > WALK_SPEED * 1.25 ? 'run' : 'walk');
    if (want !== this.animState) {
      const next = this.actions[want] ?? this.actions.idle;
      const cur = this.actions[this.animState] ?? this.actions.idle;
      next.reset().fadeIn(0.2).play();
      cur?.fadeOut(0.2);
      this.animState = want;
    }
    const ground = ANIM_GROUND_SPEED[want] ?? 1;
    const act = this.actions[want];
    if (act) act.timeScale = want === 'idle' ? 1 : THREE.MathUtils.clamp(v / ground, 0.35, 2.2);
    this.mixer.update(dt);
  }

  get up() {
    return this.pos.clone().normalize();
  }

  /* moveDir：相机相对切向单位向量（已合成 WASD）；jump：本帧是否按跳；running：是否加速 */
  update(dt, moveDir, jump, running) {
    const speed = WALK_SPEED * (running ? RUN_MULT : 1);
    this.speedNow = moveDir ? speed : 0;
    if (moveDir) {
      const step = moveOnSphere(this.pos, moveDir, speed * dt);
      this.pos.set(step.pos.x, step.pos.y, step.pos.z);
      if (Math.hypot(step.forward.x, step.forward.y, step.forward.z) > 1e-6) {
        this.forward.set(step.forward.x, step.forward.y, step.forward.z).normalize();
      }
    }
    // 径向跳跃/重力
    const wasAir = this.height > 0;
    if (jump && this.height === 0) {
      this.vSpeed = JUMP_VEL;
      this.jumpT = JUMP_STRETCH;
    }
    if (this.height > 0 || this.vSpeed > 0) {
      this.vSpeed -= GRAVITY * dt;
      this.height += this.vSpeed * dt;
      if (this.height <= 0) {
        this.height = 0;
        this.vSpeed = 0;
        if (wasAir) this.landT = LAND_SQUASH;
      }
    }
    this.updateLocomotion(dt);
    this.syncMesh(dt);
  }

  /* 程序化运动学：无绑骨模型时给整具身体加生命感 */
  updateLocomotion(dt) {
    this.updateMixer(dt);

    // GLB 模型弹入（与步态缩放互不干扰：弹入作用 modelRoot，步态作用 visual）
    if (this.modelReveal < 1) {
      this.modelReveal = Math.min(1, this.modelReveal + dt / 0.28);
      const e = 1 - Math.pow(1 - this.modelReveal, 3);
      this.modelRoot.scale.setScalar(0.6 + 0.4 * e);
    }

    if (this.mixer) return; // 绑骨模型自带全身动画，程序步态让位

    this.idleT += dt;
    const moving = this.speedNow > 0.2 && this.height === 0;
    let bobY = 0, pitch = 0, yawSway = 0, roll = 0, scaleY = 1, scaleXZ = 1;

    if (moving) {
      const k = THREE.MathUtils.clamp(this.speedNow / WALK_SPEED, 0, 1.8);
      this.walkPhase += dt * (6.2 + k * 4.6); // 步频随速度
      const s = Math.sin(this.walkPhase);
      bobY = Math.abs(s) * 0.035 * Math.min(k, 1.25);
      pitch = 0.045 * Math.min(k, 1) + Math.max(0, k - 1) * 0.05; // 走路微前倾、跑更俯
      yawSway = s * 0.05 * Math.min(k, 1);                        // 重心左右转移
      roll = Math.cos(this.walkPhase) * 0.018 * Math.min(k, 1);
    } else {
      // 待机呼吸
      const b = Math.sin(this.idleT * 1.8);
      bobY = b * 0.006;
      scaleY = 1 + b * 0.005;
    }

    if (this.height > 0) pitch += 0.04; // 空中微微提身

    // 起跳拉伸
    if (this.jumpT > 0) {
      this.jumpT -= dt;
      const j = THREE.MathUtils.clamp(this.jumpT / JUMP_STRETCH, 0, 1);
      scaleY *= 1 + 0.1 * j;
      scaleXZ *= 1 - 0.05 * j;
    }
    // 落地挤压
    if (this.landT > 0) {
      this.landT -= dt;
      const q = THREE.MathUtils.clamp(this.landT / LAND_SQUASH, 0, 1);
      const w = Math.sin(q * Math.PI);
      scaleY *= 1 - 0.16 * w;
      scaleXZ *= 1 + 0.1 * w;
      bobY -= 0.02 * w;
    }

    this.visual.position.y = bobY;
    this.visual.rotation.set(pitch, yawSway, roll); // 本地：x 前倾 / y 左右转身 / z 侧倾
    this.visual.scale.set(scaleXZ, scaleY, scaleXZ);

    // 占位小人的围巾飘带随步态摆动（GLB 围巾是网格一部分，动不了）
    if (this.tail && this.placeholder.visible) {
      this.tail.rotation.x = 0.5
        + (moving ? Math.sin(this.walkPhase) * 0.22 : Math.sin(this.idleT * 1.8) * 0.06);
    }
  }

  /* dt 缺省（出生/传送/旅行）时朝向瞬间对齐；否则指数平滑转身，消除瞬切僵尸感 */
  syncMesh(dt) {
    const up = this.up;
    // forward 正交化到当前切平面（跳跃不改变朝向）
    const f = this.forward.clone().addScaledVector(up, -this.forward.dot(up));
    if (f.lengthSq() < 1e-10) f.set(0, 0, 1).addScaledVector(up, -up.z);
    f.normalize();
    this.forward.copy(f);

    const xAxis = new THREE.Vector3().crossVectors(up, f); // 右 = up × forward
    const m = new THREE.Matrix4().makeBasis(xAxis, up, f);
    const target = new THREE.Quaternion().setFromRotationMatrix(m);
    if (dt === undefined) {
      this.mesh.quaternion.copy(target);
    } else {
      this.mesh.quaternion.slerp(target, 1 - Math.exp(-TURN_RATE * dt));
    }
    this.mesh.position.copy(this.center)
      .addScaledVector(up, this.radius + this.height);
  }
}
