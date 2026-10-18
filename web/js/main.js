/* 入口：渲染器、场景装配、主循环 */
import * as THREE from '../vendor/three.module.min.js';
import { createPlanet, PLANET_RADIUS } from './planet.js';
import { Player } from './player.js';
import { FollowCamera } from './follow-camera.js';
import { Input } from './controls.js';
import { cameraBasis, normalize, add, scale } from './sphere-math.js';

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 2000);

createPlanet(scene);

const player = new Player(scene, PLANET_RADIUS, 0, 0); // 出生在玫瑰附近
const followCam = new FollowCamera(camera);
const input = new Input();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

const clock = new THREE.Clock();

function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.05); // 切后台回来不跳变

  // 相机前向 → 角色切平面移动基
  const camDir = new THREE.Vector3();
  camera.getWorldDirection(camDir);
  const up = player.up;
  const { fwd, right } = cameraBasis(camDir, up, player.forward);

  const axis = input.axis;
  let moveDir = null;
  if (axis.x !== 0 || axis.y !== 0) {
    const d = add(scale(fwd, axis.y), scale(right, axis.x));
    const n = normalize(d);
    moveDir = n;
  }

  player.update(dt, moveDir, input.takeJump(), input.running);
  followCam.update(dt, player.mesh.position, player.forward, player.up);
  renderer.render(scene, camera);
}

frame();
