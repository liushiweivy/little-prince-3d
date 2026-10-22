/* 第三人称轨道相机：鼠标拖拽绕角色转视角（yaw）、俯仰（pitch）、滚轮缩放。
 * up 轴跟随球面法线；水平朝向 dirH 每帧投影到新切平面并平行输运，
 * 所以角色转向时镜头不会被甩动（WASD 方向永远相对当前视角）。
 * 距离/默认俯仰随当前星球半径切换。 */
import * as THREE from 'three';

const LOOK_HEIGHT = 1.15;
const LERP_RATE = 6; // 指数平滑速率
const MIN_DIST = 1.7;
const PITCH_MIN = 0.12;
const PITCH_MAX = 1.35;

const VIEWS = [
  { maxR: 5, dist: 4.2, pitch: 0.95 },          // 旅途小行星（R 3.6–4.6）：高角度近机位
  { maxR: 8, dist: 5.2, pitch: 0.48 },          // 地球（R 7）
  { maxR: Infinity, dist: 8.2, pitch: 0.39 },   // B-612（R 10）
];

export class FollowCamera {
  constructor(camera) {
    this.cam = camera;
    this.snapped = false;
    this.dirH = { x: 0, y: 0, z: 1 }; // 相机水平前向（世界系，随球面平行输运）
    this.pitch = 0.4;
    this.pitch0 = 0.4;
    this.dist = 8;
    this.maxDist = 16;
    this._desired = new THREE.Vector3();
    this._lookAt = new THREE.Vector3();
    this._f = new THREE.Vector3();
    this._up = new THREE.Vector3();
    this.setRadius(10);
  }

  setRadius(r) {
    const v = VIEWS.find(v => r <= v.maxR);
    this.dist = v.dist;
    this.pitch = v.pitch;
    this.pitch0 = v.pitch;
    this.maxDist = v.dist * 2.1;
  }

  /* 鼠标拖拽增量：yaw 绕当前 up 旋转，pitch 夹紧 */
  orbit(dx, dy) {
    const SENS = 0.0052;
    this.yaw = (this.yaw ?? 0) - dx * SENS;
    // dy>0（鼠标下拖）→ 机位抬高俯视，与 OrbitControls 的抓取手感一致
    this.pitch = THREE.MathUtils.clamp(this.pitch + dy * SENS, PITCH_MIN, PITCH_MAX);
  }

  zoom(wheelDeltaY) {
    this.dist = THREE.MathUtils.clamp(
      this.dist * Math.exp(wheelDeltaY * 0.0011), MIN_DIST, this.maxDist
    );
  }

  update(dt, pos, forward, up) {
    if (!this.snapped) {
      // 换星球/传送后的首帧：镜头贴到角色身后
      this.dirH = { x: forward.x, y: forward.y, z: forward.z };
      this.pitch = this.pitch0;
      this.yaw = 0;
      this.snapped = true;
    }

    // 先把水平前向投影到当前切平面（球面转动后去掉径向分量），再应用本帧拖拽偏航
    const f = this._f.set(this.dirH.x, this.dirH.y, this.dirH.z);
    const upV = this._up.copy(up);
    f.addScaledVector(upV, -f.dot(upV)); // projectToTangent
    if (f.lengthSq() < 1e-12) f.set(0, 1, 0);
    f.normalize();
    if (this.yaw) {
      f.applyAxisAngle(upV, this.yaw); // 与 rotateAroundAxis 同为 Rodrigues 旋转
      this.yaw = 0;
    }
    this.dirH = { x: f.x, y: f.y, z: f.z };

    const cp = Math.cos(this.pitch);
    const sp = Math.sin(this.pitch);
    const desired = this._desired.copy(pos)
      .addScaledVector(f, -this.dist * cp)
      .addScaledVector(upV, this.dist * sp);

    this.cam.position.lerp(desired, 1 - Math.exp(-LERP_RATE * dt));
    this.cam.up.copy(upV);
    this.cam.lookAt(this._lookAt.copy(pos).addScaledVector(upV, LOOK_HEIGHT));
  }
}
