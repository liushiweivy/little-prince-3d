# 错档/缺失资产清单（2026-10-22 核对）

昨晚（2026-10-22 晚）从混元旧号资产面板手工下载后按 Chrome History 归属改名，
事后 Blender 离屏渲染逐件核对，发现 **5 个资产的文件内容与名字不符**——
History 的任务 UUID 归属不可靠（资产面板 hover 弹层/新标签/查看器拦截，点击与下载内容串了）。
错档在**原档与 lite 档中内容一致**（减面流程无错），等正确原档回来后对受影响名字重跑：

```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
  --python blender/decimate_glb.py -- --only glass-dome,volcano-extinct,fountain,well,wooden-bench --force
```

## 缺失的 5 个正确资产

| 文件名 | 应是 | 摆放位置（worlds.js） | 输入参考图 | 当前文件实际内容 |
|---|---|---|---|---|
| hunyuan-glass-dome.glb | 玻璃钟罩+玫瑰+白座一体 | B-612 玫瑰位（核心道具） | hunyuan-glass-dome-input.png | 木羊箱（= sheep-box 同内容） |
| hunyuan-volcano-extinct.glb | 覆雪层状死火山锥 | B-612 死火山位 | hunyuan-volcano-extinct-input.png | 地球仪（= globe 同内容） |
| hunyuan-fountain.glb | 多层石喷泉 | 国王星王宫庭院 | （无输入图，旧号存量） | 高路灯（= streetlamp 同内容） |
| hunyuan-well.glb | 木架辘轳井 | 地球沙漠（原著结局） | hunyuan-well-input.png | 绿盘雪山/小岛（带小花与两片灰色板） |
| hunyuan-wooden-bench.glb | 木长椅（+Z 朝靠背，摆放 yaw=PI） | 地球麦海边、面朝狐狸 | hunyuan-wooden-bench-input.png | 圆座木椅（= chair 同内容） |

另有 `hunyuan-well-stone.glb`（圆石井台，未摆入游戏）内容是葡萄串，同样错档，备用资产暂不处理。

## 已验证的误判记录（防止再踩）

E:\download 下 2026-10-22 21:44–21:45 的 6 个 COS hash 文件，曾被归属为
「c1e467c4=玻璃罩玫瑰 / b5e7335e=死火山 / e0730ac8=石井 / bf69da72=石喷泉 /
f2316373=辘轳井 / 109bf201=木长椅」。渲染实证全部错误，真实内容：

| COS 对象名 | 大小 | 实际内容 | 对应正确资产 |
|---|---|---|---|
| c1e467c4c907df601c6520eee0334140.glb | 41,134,184 | 木羊箱 | sheep-box |
| b5e7335e538ef3901b1cb10fd3905558.glb | 47,105,864 | 地球仪 | globe（dl_props.sh 本就把它下给 globe） |
| e0730ac81100a2bafe40afa31c977053.glb | 40,971,252 | 葡萄串 | grapes |
| bf69da721c671247214392affae1e48e.glb | 37,852,756 | 高路灯（底座带小灯） | streetlamp（重提版） |
| f23163733bf5c1ed820f3c92f74c9010.glb | 45,094,508 | 绿盘雪山小岛 | 无对应（疑似地形测试产物） |
| 109bf201d81ce7305b5f07352f42a11b.glb | 38,836,112 | 圆座木椅 | chair |

`_web_jobs.json` 里 9525c656 / 3d12c8bf / e25f7906 / 55ee4815 / 6db9ac35 这批
`*-cddf-11f1-8319-32f6c13eda4a` 的「旧号手工下载」id 与名称映射也不可信
（dl_props.sh 的 COS 路径佐证：3d12c8bf 产物是地球仪、e25f7906 产物是绿盘）。

## 恢复步骤

1. 混元网页版登录旧号 → https://3d.hunyuan.tencent.com/assets
2. **按缩略图肉眼找**玻璃罩玫瑰 / 覆雪死火山 / 多层石喷泉 / 木架辘轳井 / 木长椅
   （不要信任何 id/History 归属；缩略图透明底，深色喷泉多看两眼）
3. 逐张「查看模型」确认 3D 内容无误后再下载 GLB（COS 签名直链 24h 有效，
   页内 `GET /api/3d/creations/detail?creationsId=<uuid>` 取 result[0].urlResult.glb，
   curl 必须 `--noproxy '*'`）
4. 下载后**先 Blender 渲染验证**再改名入位（可复用 `blender/idl_check.py` 改路径，
   或 `blender/render_check.py`）
5. 覆盖 web/models 下错档 → 按上面命令 `--force` 重跑减面 → 再渲染 lite 对比
6. 若旧号资产库里根本没有这 5 件，用各自 input.png 在网页版重新生成（500k 档，
   提交后先核对档位真的切到 500k，见记忆 hunyuan3d-web-download 酒瓶教训）
