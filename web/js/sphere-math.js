/* 球面行走数学层：纯函数，只读写 {x,y,z} 结构，不依赖 three，Node 可直接单测。
 * 约定：星球中心在原点，角色位置 pos 的模长 = 星球半径 R，up = normalize(pos)。 */

export const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
export const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
export const scale = (a, s) => ({ x: a.x * s, y: a.y * s, z: a.z * s });
export const dot = (a, b) => a.x * b.x + a.y * b.y + a.z * b.z;
export const cross = (a, b) => ({
  x: a.y * b.z - a.z * b.y,
  y: a.z * b.x - a.x * b.z,
  z: a.x * b.y - a.y * b.x,
});
export const length = (a) => Math.hypot(a.x, a.y, a.z);

export function normalize(a) {
  const l = length(a);
  if (l < 1e-12) return { x: 0, y: 1, z: 0 }; // 零向量兜底为上方向，避免 NaN 扩散
  return scale(a, 1 / l);
}

/* 把任意方向 dir 投影到 up 处的切平面（去掉径向分量） */
export function projectToTangent(dir, up) {
  return sub(dir, scale(up, dot(dir, up)));
}

/* Rodrigues 公式：v 绕单位轴 axis 旋转 angle 弧度 */
export function rotateAroundAxis(v, axis, angle) {
  const k = normalize(axis);
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  return add(
    add(scale(v, c), scale(cross(k, v), s)),
    scale(k, dot(k, v) * (1 - c))
  );
}

/* 沿球面大圆行走：从 pos 朝 dir（切向）走 dist 弧长。
 * 返回新的 pos 与随球面平行移动后的 forward（保持单位切向）。 */
export function moveOnSphere(pos, dir, dist) {
  const R = length(pos);
  const up = normalize(pos);
  let tangent = projectToTangent(dir, up);
  if (length(tangent) < 1e-8 || dist === 0) {
    return { pos: { ...pos }, forward: tangent };
  }
  tangent = normalize(tangent);
  const axis = cross(up, tangent); // up⊥tangent 且均单位 → axis 即单位轴
  const angle = dist / R;
  return {
    pos: rotateAroundAxis(pos, axis, angle),
    forward: rotateAroundAxis(tangent, axis, angle),
  };
}

/* 纬度/经度（度）→ 单位方向。lat=90 为 +Y 极点，lon 绕 Y 轴。 */
export function latLonToDir(latDeg, lonDeg) {
  const la = (latDeg * Math.PI) / 180;
  const lo = (lonDeg * Math.PI) / 180;
  return {
    x: Math.cos(la) * Math.cos(lo),
    y: Math.sin(la),
    z: Math.cos(la) * Math.sin(lo),
  };
}

/* 相机前向 → 角色处切平面内的移动基（前/右），退化时兜底用角色朝向 */
export function cameraBasis(camDir, up, fallbackForward) {
  let fwd = projectToTangent(camDir, up);
  if (length(fwd) < 1e-6) {
    fwd = projectToTangent(fallbackForward, up);
  }
  fwd = normalize(fwd);
  const right = normalize(cross(fwd, up));
  return { fwd, right };
}
