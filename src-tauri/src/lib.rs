// 桌面壳入口（lib 形态，方便后续移动端/测试复用）。
// 纯静态页面无需任何 Tauri 插件/命令：同源 tauri.localhost 下 fetch GLB 即可。
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("启动小王子桌面版失败");
}
