/* 球面数学层单测：node --test tools/test_sphere.mjs（Node24 须显式文件路径） */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  dot, cross, length, normalize, projectToTangent,
  rotateAroundAxis, moveOnSphere, latLonToDir, cameraBasis,
} from '../web/js/sphere-math.js';

const R = 10;
const close = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) < eps, `${a} !~ ${b}`);
const vClose = (a, b, eps = 1e-6) => {
  close(a.x - b.x, 0, eps); close(a.y - b.y, 0, eps); close(a.z - b.z, 0, eps);
};

test('normalize：单位化，零向量兜底为上方向', () => {
  const n = normalize({ x: 3, y: 0, z: 4 });
  close(length(n), 1);
  vClose(normalize({ x: 0, y: 0, z: 0 }), { x: 0, y: 1, z: 0 });
});

test('projectToTangent：结果与 up 正交，切向分量保留', () => {
  const up = { x: 0, y: 1, z: 0 };
  const t = projectToTangent({ x: 1, y: 2, z: 1 }, up);
  close(dot(t, up), 0);
  vClose(t, { x: 1, y: 0, z: 1 });
});

test('rotateAroundAxis：绕 Y 轴转 90 度，模长不变', () => {
  const v = rotateAroundAxis({ x: 1, y: 0, z: 0 }, { x: 0, y: 1, z: 0 }, Math.PI / 2);
  close(length(v), 1);
  vClose(v, { x: 0, y: 0, z: -1 }, 1e-9);
});

test('moveOnSphere：位置保持球面半径，forward 保持单位切向', () => {
  const pos = { x: R, y: 0, z: 0 };
  const step = moveOnSphere(pos, { x: 0, y: 0, z: 1 }, 1.5);
  close(length(step.pos), R, 1e-9);
  const up = normalize(step.pos);
  close(dot(step.forward, up), 0, 1e-9);
  close(length(step.forward), 1, 1e-9);
});

test('moveOnSphere：沿大圆走整圈回到出发点', () => {
  let pos = { x: R, y: 0, z: 0 };
  let fwd = { x: 0, y: 0, z: 1 };
  const steps = 360;
  const arc = (2 * Math.PI * R) / steps;
  for (let i = 0; i < steps; i++) {
    const s = moveOnSphere(pos, fwd, arc);
    pos = s.pos; fwd = s.forward;
  }
  vClose(pos, { x: R, y: 0, z: 0 }, 1e-6);
  vClose(fwd, { x: 0, y: 0, z: 1 }, 1e-6);
});

test('moveOnSphere：四分之一圈后 up 转过 90 度', () => {
  const pos = { x: R, y: 0, z: 0 };
  const s = moveOnSphere(pos, { x: 0, y: 0, z: 1 }, (Math.PI / 2) * R);
  vClose(normalize(s.pos), { x: 0, y: 0, z: 1 }, 1e-9);
  vClose(s.forward, { x: -1, y: 0, z: 0 }, 1e-9);
});

test('moveOnSphere：径向输入（无切向分量）位置不动', () => {
  const pos = { x: 0, y: R, z: 0 };
  const s = moveOnSphere(pos, { x: 0, y: 1, z: 0 }, 2);
  vClose(s.pos, pos);
});

test('moveOnSphere：dist=0 位置不变', () => {
  const pos = { x: R, y: 0, z: 0 };
  const s = moveOnSphere(pos, { x: 0, y: 0, z: 1 }, 0);
  vClose(s.pos, pos);
});

test('latLonToDir：单位向量，极点与赤道正确', () => {
  vClose(latLonToDir(90, 0), { x: 0, y: 1, z: 0 }, 1e-9);
  vClose(latLonToDir(0, 0), { x: 1, y: 0, z: 0 }, 1e-9);
  vClose(latLonToDir(0, 90), { x: 0, y: 0, z: 1 }, 1e-9);
  close(length(latLonToDir(37, 123)), 1, 1e-9);
});

test('cameraBasis：前/右基正交单位且在切平面内', () => {
  const up = { x: 0, y: 1, z: 0 };
  const { fwd, right } = cameraBasis({ x: 0, y: -0.5, z: -1 }, up, { x: 0, y: 0, z: 1 });
  close(length(fwd), 1); close(length(right), 1);
  close(dot(fwd, right), 0, 1e-9);
  close(dot(fwd, up), 0, 1e-9);
  // 相机朝 -Z 看、up 为 +Y 时，右应为 +X
  vClose(fwd, { x: 0, y: 0, z: -1 }, 1e-9);
  vClose(right, { x: 1, y: 0, z: 0 }, 1e-9);
});

test('cameraBasis：相机垂直俯视（退化）时回退到角色朝向', () => {
  const up = { x: 0, y: 1, z: 0 };
  const { fwd } = cameraBasis({ x: 0, y: -1, z: 0 }, up, { x: 0, y: 0, z: 1 });
  vClose(fwd, { x: 0, y: 0, z: 1 }, 1e-9);
});

test('cross：右手系', () => {
  vClose(cross({ x: 1, y: 0, z: 0 }, { x: 0, y: 1, z: 0 }), { x: 0, y: 0, z: 1 });
});
