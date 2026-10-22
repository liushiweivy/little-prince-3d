# 小王子 3D 网页漫游 —— 工作流与最小 Demo

在小行星 B612 上自由行走（球面重力 + 第三人称跟随相机）的网页小游戏，现已有 B-612 + 旅途六星 + 地球共 8 个星球、10 段原著对话、星图旅行，并提供 **Tauri 桌面版**（双击即玩，无需浏览器/服务器）。
本仓库按「先 Three.js 原型跑通玩法 → 再上美术资产 → 最后 Unity WebGL 定版」的节奏推进。

## 桌面版（Tauri v2）

```bat
play.bat          :: 双击即玩（无 exe 时自动构建，首次编译依赖约 10-20 分钟）
```

- 游戏本体是纯静态页面（web/），桌面壳只嵌 WebView2（系统已装，免引导器）。
- 构建产物：`src-tauri/target/release/little-prince.exe`（双击即玩）+ NSIS 安装包 `.../bundle/nsis/`（NSIS 工具链从 GitHub 下载，本机网络超时则跳过安装包只留 exe，网络好后重跑 `npm run tauri:build` 自动续）。
- 桌面版只打包 **lite 减面档**（`web/models/lite/`，~84MB）+ glass-dome full 档（assets.js LITE_SKIP 玻璃材质豁免）+ triposr 三小档，白名单由 `tools/prepare_app_dist.py` 生成到 `dist-app/`（构建前自动执行）。
- 重建依赖：Rust（cargo）+ Node（@tauri-apps/cli devDependency）+ Python312（dist 脚本路径在 package.json `app:dist`，换机需改）。
- `npm run tauri:dev` 是开发模式：需**先起 8850 开发服务器**（start.bat）再跑，窗口加载 devUrl。

## 资产档位：lite（默认）/ full

- 混元原档每个 50 万面 + 3 张 4096² PNG（全场 1076MB），导致越玩越卡。
- 现默认加载 `web/models/lite/` 减面档（83.6MB / 62.5 万面，贴图 1024²），按星球懒加载、离开即 dispose。
- 回退原档：URL 加 `?assets=full`（切档开关在 `web/js/assets.js`，只重写 `hunyuan-*.glb` 路径）。
- 重生成 lite：`blender.exe --background --python blender/decimate_glb.py -- [--only a,b] [--force] [--tex 1024]`（原档保留不覆盖）。
- ⚠️ 已知错档（2026-10-22）：玻璃罩玫瑰/死火山/喷泉/辘轳井/木长椅 5 个源文件内容是其他道具的替身，清单与恢复步骤见 `assets/input/MISSING_ASSETS.md`（不影响运行，影响还原度）。

## 一、最小 Demo 环境清单（本机已具备 ✅）

| 项 | 用途 | 本机情况 |
|---|---|---|
| 浏览器 (Edge/Chrome) | 运行原型 | ✅ |
| Node 24 | 跑数学层单元测试 | ✅ v24.12.0 |
| Python 3.x | 起静态服务器 | ✅ 任意发行版；本机 `python` 命令异常时在项目根放 `python-path.txt`（gitignore）写解释器全路径 |
| Three.js r180 本地 vendor | 渲染引擎（离线零依赖，从 mini-aram 复用） | ✅ `web/vendor/` |

> 启动：双击 `start.bat` → 浏览器打开 http://127.0.0.1:8850/

## 二、完整管线城市清单（后续逐步装）

| 工具 | 用途 | 备注 |
|---|---|---|
| **Opus (Claude)** | 写代码 + Tripo/Blender 提示词 | 已在用 |
| **Tripo AI** | 文/图生 3D 模型（小王子、玫瑰、猴面包树、狐狸…） | 网页版，导出 GLB |
| **Blender 4.x** | 修模：减面、烘焙贴图、骨骼/动画、统一比例导出 GLB | 便携版即可 |
| **Unity 6 (LTS) + WebGL Build Support** | 定版工程：URP、角色控制器、导出 WebGL 网页游戏 | 装 Unity Hub → 安装时勾选 WebGL 模块 |

### 资产流水线（每个模型走一遍）

```
Opus 写提示词 → Tripo 生成 GLB → Blender 修模/减面/归一比例
  → (A) Three.js 原型直接加载 GLB 快速验证
  → (B) Unity 导入 → 材质/碰撞/动画 → Build: WebGL → 部署静态页
```

比例约定：角色高 1.1 单位，星球半径 10 单位，Blender 导出时统一 Apply Scale。

## 三、项目目录

```
little-prince-3d/
├── README.md            ← 本文件（工作流总览）
├── start.bat            ← 一键起本地服务 :8850（内容纯 ASCII）
├── web/                 ← Three.js 最小原型（当前阶段）
│   ├── index.html
│   ├── css/style.css
│   ├── js/
│   │   ├── main.js          入口/主循环
│   │   ├── sphere-math.js   球面数学（纯函数，Node 可测）
│   │   ├── planet.js        星球+玫瑰/猴面包树/火山/星空
│   │   ├── player.js        小王子角色+球面移动/跳跃
│   │   ├── follow-camera.js 第三人称跟随相机
│   │   └── controls.js      键鼠输入
│   └── vendor/              three.module.min.js r180 + core + LICENSE
├── tools/
│   └── test_sphere.mjs  ← 球面数学单测（node --test）
├── assets/
│   ├── models/          ← Tripo 产出的 GLB（占位）
│   └── prompts/         ← Tripo/美术提示词库（占位）
├── blender/             ← 修模脚本与 .blend 工程（占位）
└── unity/               ← Unity WebGL 工程（占位，定版阶段启用）
```

## 四、原型操作

| 按键 | 动作 |
|---|---|
| W A S D / 方向键 | 沿星球表面行走（相机相对方向） |
| Space | 跳跃 |
| Shift | 加速跑 |
| 绕星球走一圈 | 约 16 秒（星球半径 10） |

## 五、测试

```bash
node --test tools/test_sphere.mjs   # 球面数学层（不依赖 three）
```

## 六、路线图

1. ✅ M0：Three.js 球面行走原型（本次）
2. ✅ M1：混元 3D 出小王子/NPC/道具 GLB → Blender 修模 → 原型内 GLTFLoader 加载
3. ✅ M2：玩法层（8 星球星图旅行、10 段对话、右键寻路）
4. ✅ M2.5：性能治理（lite 减面 83.6MB/62.5 万面 + 按星懒加载 dispose）+ Tauri v2 桌面版
5. ⬜ M3：Unity 工程重建 + WebGL 导出定版（或继续打磨 Three.js 版）
