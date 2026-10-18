# 小王子 3D 网页漫游 —— 工作流与最小 Demo

在小行星 B612 上自由行走（球面重力 + 第三人称跟随相机）的网页小游戏。
本仓库按「先 Three.js 原型跑通玩法 → 再上美术资产 → 最后 Unity WebGL 定版」的节奏推进。

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
2. ⬜ M1：Tripo 出小王子/玫瑰/狐狸 GLB → Blender 修模 → 原型内 GLTFLoader 加载替换几何体
3. ⬜ M2：玩法层（多星球跳跃/收集星星/对话气泡）
4. ⬜ M3：Unity 工程重建 + WebGL 导出定版
