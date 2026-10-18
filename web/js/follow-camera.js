/* 第三人称跟随相机：挂在角色身后上方，up 轴跟随球面法线 */
import * as THREE from '../vendor/three.module.min.js';

const DIST = 7.5;
const HEIGHT = 3.0;
const LOOK_HEIGHT = 1.2;
const LERP_RATE = 6; // 指数平滑速率

export class FollowCamera {
  constructor(camera) {
    this.cam = camera;
    this.snapped = false;
  }

  update(dt, pos, forward, up) {
    const desired = pos.clone()
      .addScaledVector(forward, -DIST)
      .addScaledVector(up, HEIGHT);
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
