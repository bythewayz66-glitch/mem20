// mem20controlz Tauri shell entry point (issue #35).
//
// The binary does one thing: hand control to the library. The previous
// scaffold built its own `tauri::Builder` here and never called
// `mem20controlz_desktop_lib::run()`, so the lib — and the `probe_control_plane`
// command registered inside it — was dead code that no binary ever ran.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    mem20controlz_desktop_lib::run();
}
