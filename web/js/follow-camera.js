/* 第三人称跟随相机：挂在角色身后上方，up 轴跟随球面法线。
 * 距离/抬高随当前星球半径切换（小行星用高角度近机位才能看见近处 NPC）。 */
import * as THREE from 'three';

const LOOK_HEIGHT = 1.2;
const LERP_RATE = 6; // 指数平滑速率

const VIEWS = [
  { maxR: 5, dist: 2.4, height: 3.4 },  // 旅途小行星（R 3.6–4.6）
  { maxR: 8, dist: 4.6, height: 2.4 },  // 地球（R 7）
  { maxR: Infinity, dist: 7.5, height: 3.0 }, // B-612（R 10）
];

export class FollowCamera {
  constructor(camera) {
    this.cam = camera;
    this.snapped = false;
    this.setRadius(10);
  }

  setRadius(r) {
    const v = VIEWS.find(v => r <= v.maxR);
    this.dist = v.dist;
    this.height = v.height;
  }

  update(dt, pos, forward, up) {
    const desired = pos.clone()
      .addScaledVector(forward, -this.dist)
      .addScaledVector(up, this.height);
    if (!this.snapped) {
      this.cam.position.copy(desired);
      this.snapped = true;
    } else {
      this.cam.position.lerp(desired, 1 - Math.exp(-LERP_RATE * dt));
    }
    this.cam.up.copy(up);
    const target = pos.clone().addScaledVector(up, LOOK_HEIGHT);
    this.cam.lookAt(target);
  }
}
