/* 入口：渲染器、多星球装配、星图旅行、主循环 */
import * as THREE from '../vendor/three.module.min.js';
import { createWorlds } from './worlds.js';
import { Player } from './player.js';
import { FollowCamera } from './follow-camera.js?v=4';
import { Input } from './controls.js';
import { DialogueUI } from './dialogue-ui.js';
import { DIALOGUES } from './dialogues.js';
import { cameraBasis, normalize, add, scale, latLonToDir } from './sphere-math.js';

const TALK_RANGE = 2.6; // 离 NPC 多近可以按 E 交谈

const FADE_OUT = 0.62;   // 淡出时长（秒）
const DESCEND = 1.9;    // 落点高度 → 地面
const START_HEIGHT = 7; // 抵达星球时的初始高度

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 2000);

const { list: worlds, byId } = createWorlds(scene);
let current = byId.get('b612');

const player = new Player(scene, {
  center: current.center,
  radius: current.def.radius,
  spawn: current.def.spawn,
});
const followCam = new FollowCamera(camera);
const input = new Input();
const dialogue = new DialogueUI();

const planetNameEl = document.getElementById('planet-name');
const padPromptEl = document.getElementById('pad-prompt');
const starmapEl = document.getElementById('starmap');
const starmapListEl = document.getElementById('starmap-list');
const fadeEl = document.getElementById('fade');
fadeEl.style.transition = 'opacity 0.6s ease';

/* 星图：列出所有星球，点击即启程 */
let mapOpen = false;
function renderMap() {
  starmapListEl.innerHTML = '';
  for (const w of worlds) {
    const btn = document.createElement('button');
    btn.className = 'starmap-item' + (w === current ? ' current' : '');
    const label = w.def.name
      .replace(/^\d+ 号行星 · /, '')
      .replace(/^B-612 小行星$/, '玫瑰与三座火山')
      .replace(/^地球 · /, '');
    btn.innerHTML = `<span class="num">${w.def.num}</span><span>${label}</span>`;
    if (w === current) {
      btn.querySelector('span:last-child').textContent = '当前所在';
      btn.disabled = true;
    } else {
      btn.addEventListener('click', () => startTravel(w));
    }
    starmapListEl.appendChild(btn);
  }
}
function openMap() {
  mapOpen = true;
  renderMap();
  starmapEl.classList.remove('hidden');
  padPromptEl.classList.add('hidden');
}
function closeMap() {
  mapOpen = false;
  starmapEl.classList.add('hidden');
}

/* 交谈：NPC 在自身切平面内转身面向玩家，再打开对话面板 */
function startDialogue(npc) {
  if (!DIALOGUES[npc.key]) return; // 未配对话的 NPC 按 E 不应表现成卡住
  const n = npc.anchor.position.clone().normalize();
  const f = player.pos.clone().addScaledVector(n, -player.pos.dot(n));
  if (f.lengthSq() > 1e-8) {
    f.normalize();
    const x = new THREE.Vector3().crossVectors(n, f);
    npc.anchor.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, n, f));
  }
  padPromptEl.classList.add('hidden');
  dialogue.start(npc);
}

/* 旅行过场：淡出 → 换星球（从高处出现）→ 淡入 + 落下 */
const travel = { active: false, phase: null, t: 0, target: null };
function startTravel(world) {
  if (travel.active || world === current) return;
  closeMap();
  travel.active = true;
  travel.phase = 'out';
  travel.t = 0;
  travel.target = world;
  fadeEl.style.opacity = '1';
}
function arriveOn(world) {
  current = world;
  travel.phase = 'descend'; // 先切阶段，避免后续异常导致每帧重复进场
  travel.t = 0;
  player.travelTo({ center: world.center, radius: world.def.radius, spawn: world.def.spawn }, START_HEIGHT);
  followCam.setRadius(world.def.radius);
  followCam.snapped = false; // 相机立刻贴到新落点身后，下帧起跟随下落
  planetNameEl.innerHTML = `小王子 <span>·</span> ${world.def.name}`;
  fadeEl.style.opacity = '0';
}

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// 调试钩子：控制台 __debug.teleport(lat, lon) / __debug.go('king')
window.__debug = {
  player, worlds,
  teleport(latDeg, lonDeg) {
    const d = latLonToDir(latDeg, lonDeg);
    player.pos.set(d.x, d.y, d.z).multiplyScalar(current.def.radius);
    player.height = 0; player.vSpeed = 0;
    player.syncMesh();
    followCam.snapped = false;
  },
  go(id) { startTravel(byId.get(id)); },
};

// 出发台光柱：旋转 + 呼吸
const beams = worlds.map(w => w.group.getObjectByName('padBeam')).filter(Boolean);

const clock = new THREE.Clock();
let elapsed = 0;

function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.05); // 切后台回来不跳变
  elapsed += dt;

  if (travel.active) {
    travel.t += dt;
    if (travel.phase === 'out' && travel.t >= FADE_OUT) {
      arriveOn(travel.target);
    } else if (travel.phase === 'descend') {
      const k = Math.min(travel.t / DESCEND, 1);
      const eased = 1 - (1 - k) * (1 - k);
      player.tickTravel(dt, START_HEIGHT * (1 - eased));
      if (k >= 1) {
        travel.active = false;
        input.flush(); // 过场期间按的键不许在落点第一帧触发
      }
    } else {
      input.flush();
    }
  } else if (mapOpen) {
    // 星图打开时原地待机
    player.tickTravel(dt, 0);
    if (input.takeCancel()) {
      closeMap();
      input.flush(); // 关图同帧丢弃残留 E，防止立刻重开/误开对话
    } else {
      input.takeInteract();
      input.takeJump();
    }
  } else if (dialogue.active) {
    // 对话中原地待机；推进/结束由 DialogueUI 消费按键
    player.tickTravel(dt, 0);
    dialogue.update(dt, input);
  } else {
    // 相机前向 → 角色切平面移动基
    const camDir = new THREE.Vector3();
    camera.getWorldDirection(camDir);
    const up = player.up;
    const { fwd, right } = cameraBasis(camDir, up, player.forward);

    const axis = input.axis;
    let moveDir = null;
    if (axis.x !== 0 || axis.y !== 0) {
      moveDir = normalize(add(scale(fwd, axis.y), scale(right, axis.x)));
    }

    player.update(dt, moveDir, input.takeJump(), input.running);

    // 找最近的可交谈 NPC
    let nearNpc = null;
    let nearDist = TALK_RANGE;
    for (const npc of current.npcs) {
      const wp = current.center.clone().add(npc.anchor.position);
      const d = player.worldPos.distanceTo(wp);
      if (d < nearDist) { nearDist = d; nearNpc = npc; }
    }

    // E：身边有人先交谈，否则打开星图
    if (input.takeInteract()) {
      if (nearNpc) startDialogue(nearNpc);
      else openMap();
    }

    // 上下文提示：对话中始终隐藏；否则交谈优先于出发台
    const nearPad = player.worldPos.distanceTo(current.padWorld) < 2.4;
    let promptHtml = null;
    if (!dialogue.active) {
      if (nearNpc) promptHtml = `按 <b>E</b> 与「${nearNpc.label}」交谈`;
      else if (nearPad) promptHtml = '按 <b>E</b> 打开星图出发';
    }
    if (promptHtml === null) {
      padPromptEl.classList.add('hidden');
    } else {
      if (padPromptEl.innerHTML !== promptHtml) padPromptEl.innerHTML = promptHtml;
      padPromptEl.classList.remove('hidden');
    }
  }

  for (const beam of beams) {
    beam.rotation.y += dt * 0.7;
    beam.material.opacity = 0.1 + 0.045 * Math.sin(elapsed * 2.6);
  }

  followCam.update(dt, player.mesh.position, player.forward, player.up);
  renderer.render(scene, camera);
}

frame();
