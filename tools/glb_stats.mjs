// GLB 批量体检：面数 / 网格 / 材质 / 贴图 / 骨骼 / 文件大小（只读 JSON chunk）。
// 用法：node tools/glb_stats.mjs [models|lite|<目录>]，默认 models（web/models 根）。
import { readFileSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = fileURLToPath(new URL('.', import.meta.url));
const arg = process.argv[2] || 'models';
const dir = resolve(here, '..', 'web', arg === 'models' || arg === 'lite' ? `models/${arg === 'lite' ? 'lite' : ''}` : arg);

function readGlb(file) {
  const buf = readFileSync(file);
  const jsonLen = buf.readUInt32LE(12);
  const json = JSON.parse(buf.slice(20, 20 + jsonLen).toString('utf8'));
  let tris = 0;
  let meshes = 0;
  for (const m of json.meshes ?? []) {
    meshes++;
    for (const p of m.primitives) {
      const acc = p.indices !== undefined ? json.accessors[p.indices] : null;
      if (acc) tris += acc.count / 3;
      else if (p.attributes?.POSITION) tris += json.accessors[p.attributes.POSITION].count / 3;
    }
  }
  const images = (json.images ?? []).map((i) => {
    const view = i.bufferView !== undefined ? json.bufferViews[i.bufferView] : null;
    return { mime: i.mimeType ?? 'uri', bytes: view?.byteLength ?? 0 };
  });
  return {
    bytes: buf.length,
    meshes,
    tris: Math.round(tris),
    materials: (json.materials ?? []).length,
    skins: (json.skins ?? []).length,
    images: images.length,
    imgBytes: images.reduce((s, i) => s + i.bytes, 0),
    mimes: [...new Set(images.map((i) => i.mime))].join(','),
  };
}

const files = readdirSync(dir).filter((f) => f.endsWith('.glb')).sort();
const rows = files.map((f) => ({ f, ...readGlb(join(dir, f)) })).sort((a, b) => b.tris - a.tris);
console.log(`dir: ${dir}（${rows.length} 个 GLB）`);
console.log('file'.padEnd(32), 'MB'.padStart(6), 'tris'.padStart(8), 'mesh'.padStart(5), 'mat'.padStart(4),
  'skin'.padStart(4), 'img'.padStart(4), 'imgMB'.padStart(6), 'mime');
let totBytes = 0, totTris = 0, totImg = 0;
for (const r of rows) {
  totBytes += r.bytes; totTris += r.tris; totImg += r.imgBytes;
  console.log(r.f.padEnd(32), (r.bytes / 1048576).toFixed(2).padStart(6), String(r.tris).padStart(8),
    String(r.meshes).padStart(5), String(r.materials).padStart(4), String(r.skins).padStart(4),
    String(r.images).padStart(4), (r.imgBytes / 1048576).toFixed(2).padStart(6), r.mimes);
}
console.log('-'.repeat(86));
console.log('TOTAL'.padEnd(32), (totBytes / 1048576).toFixed(1).padStart(6), String(totTris).padStart(8),
  '', '', '', '', (totImg / 1048576).toFixed(1).padStart(6));
