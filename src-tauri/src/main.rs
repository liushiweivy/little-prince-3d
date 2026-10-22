// 小王子：星辰之旅 — Tauri v2 桌面壳。
// 游戏本体是纯静态 Three.js 页面（dist-app/，构建时白名单生成），
// 无任何自定义命令/插件：窗口 + WebView2 即全部原生部分。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    little_prince_lib::run()
}
