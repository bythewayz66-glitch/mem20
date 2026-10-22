// mem20controlz Tauri shell scaffold (issue #35)
// Reuses the existing React/static bundle. Sidecar = issue #36; signing = #40.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running mem20controlz");
}
