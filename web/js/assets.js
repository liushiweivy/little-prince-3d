/* 资产档位开关：默认用 lite（Blender 减面 + 1024 贴图，web/models/lite/），
 * ?assets=full 回退 web/models/ 原档（混元 50 万面/4K 贴图）。
 * 只有 hunyuan-*.glb 有 lite 版本；triposr 旧档/绑骨档等保持原路径。 */
const params = new URLSearchParams(location.search);
export const ASSETS_LITE = params.get('assets') !== 'full';

/* lite 减面回归豁免：玻璃钟罩在 lite 档（1024 贴图）下罩体与红玫瑰几乎不可见，
 * 暂走 full 原档，待减面管线修玻璃材质后移除（2026-10-22 实测）。 */
const LITE_SKIP = new Set(['hunyuan-glass-dome.glb']);

export function assetPath(p) {
  if (!ASSETS_LITE) return p;
  const name = p.split('/').pop();
  if (LITE_SKIP.has(name)) return p;
  return /^hunyuan-.*\.glb$/.test(name) ? `./models/lite/${name}` : p;
}
