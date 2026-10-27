//! Tauri-facing half of the tray: menu, tooltip, notification, quit.
//!
//! Issue #37. Everything decision-shaped lives in `mem20desktop::tray` and
//! `mem20desktop::poller`; this file only paints what those decided. That split
//! is what lets the false-alarm rules be tested on a machine with no WebView.
//!
//! This module would be the wrong place to re-derive "is this worth a toast":
//! that rule is `FleetHealth::is_notification_worthy`, which is table-tested.

use std::sync::{Arc, Mutex};

use tauri::menu::{CheckMenuItem, Menu, MenuItem};
use tauri::tray::{MouseButton, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Manager, Runtime};
use tauri_plugin_notification::NotificationExt;

use mem20desktop::poller::{self, Tick};
use mem20desktop::tray::{FleetHealth, Notification, NotificationEngine};

/// Tray item id, so the glyph can be repainted without rebuilding the tray.
pub const TRAY_ID: &str = "mem20-fleet";

/// Shared state owned by the Tauri app.
pub struct TrayState {
    pub engine: Mutex<NotificationEngine>,
    pub last: Mutex<Option<FleetHealth>>,
    pub muted: Mutex<bool>,
}

impl Default for TrayState {
    fn default() -> Self {
        Self {
            engine: Mutex::new(NotificationEngine::new()),
            last: Mutex::new(None),
            muted: Mutex::new(false),
        }
    }
}

/// Build the tray once, from `setup`, so it exists before any window closes and
/// is never torn down with a window (AC-37-13).
pub fn install<R: Runtime>(app: &AppHandle<R>, muted_at_startup: bool) -> tauri::Result<()> {
    let show = MenuItem::with_id(app, "show", "Open mem20 control plane", true, None::<&str>)?;
    let mute = CheckMenuItem::with_id(
        app,
        "mute",
        "Mute notifications",
        true,
        muted_at_startup,
        None::<&str>,
    )?;
    let quit = MenuItem::with_id(app, "quit", "Quit mem20", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &mute, &quit])?;

    let mute_item = mute.clone();

    TrayIconBuilder::with_id(TRAY_ID)
        // Pre-first-tick text only; no age is claimed because none was measured.
        .tooltip(FleetHealth::Starting.tooltip(f64::NAN, false))
        .icon(
            app.default_window_icon()
                .cloned()
                .ok_or_else(|| tauri::Error::AssetNotFound("tray icon asset".into()))?,
        )
        .menu(&menu)
        // Left click opens the window; the menu is the right-click surface.
        .show_menu_on_left_click(false)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "show" => reveal_window(app),
            "mute" => {
                let muted = mute_item.is_checked().unwrap_or(false);
                apply_mute(app, muted);
                persist_muted(app, muted);
            }
            // Explicit quit. `app.exit` runs RunEvent::Exit, where #36's sidecar
            // supervisor tears the child down -- it must not be orphaned
            // (AC-37-16).
            "quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click { button, .. } = event {
                if button == MouseButton::Left {
                    reveal_window(tray.app_handle());
                }
            }
        })
        .build(app)?;

    apply_mute(app, muted_at_startup);
    Ok(())
}

/// Show and focus the existing window rather than opening a second one.
fn reveal_window<R: Runtime>(app: &AppHandle<R>) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

/// Mute silences alerts only; the glyph keeps telling the truth (AC-37-11).
/// Silencing the indicator too would leave the user with no signal at all.
fn apply_mute<R: Runtime>(app: &AppHandle<R>, muted: bool) {
    if let Some(state) = app.try_state::<Arc<TrayState>>() {
        if let Ok(mut flag) = state.muted.lock() {
            *flag = muted;
        }
        if let Ok(mut engine) = state.engine.lock() {
            engine.set_muted(muted);
        }
    }
}

fn mute_path<R: Runtime>(app: &AppHandle<R>) -> Option<std::path::PathBuf> {
    app.path()
        .app_config_dir()
        .ok()
        .map(|dir| dir.join("tray-muted"))
}

/// Persist the mute flag so the checkmark is correct after a relaunch.
fn persist_muted<R: Runtime>(app: &AppHandle<R>, muted: bool) {
    if let Some(path) = mute_path(app) {
        if let Some(parent) = path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        let _ = std::fs::write(path, if muted { "1" } else { "0" });
    }
}

/// Read the persisted mute flag at startup.
pub fn load_muted<R: Runtime>(app: &AppHandle<R>) -> bool {
    mute_path(app)
        .and_then(|path| std::fs::read_to_string(path).ok())
        .map(|raw| raw.trim() == "1")
        .unwrap_or(false)
}

/// Paint one poll result: tooltip, remembered verdict, at most one toast.
pub fn apply<R: Runtime>(app: &AppHandle<R>, result: &poller::PollResult) {
    let glyph = result.tick.glyph();
    let (age_s, stale) = match &result.tick {
        Tick::Registry(payload) => (payload.age_s, mem20desktop::tray::is_stale(payload)),
        // Nothing was measured, so no age may be claimed.
        _ => (f64::NAN, false),
    };

    if let Some(tray) = app.tray_by_id(TRAY_ID) {
        // Leads with the probe age, not with "last refresh succeeded": those
        // differ by the cache age and conflating them is how a stale reading
        // gets presented as live (AC-37-04).
        let _ = tray.set_tooltip(Some(glyph.tooltip(age_s, stale)));
    }

    if let Some(state) = app.try_state::<Arc<TrayState>>() {
        if let Ok(mut last) = state.last.lock() {
            *last = Some(glyph);
        }
    }

    if let Some(notification) = &result.notification {
        raise(app, notification);
    }
}

/// Raise exactly the one notification the engine decided on.
fn raise<R: Runtime>(app: &AppHandle<R>, notification: &Notification) {
    // A blank toast reads as a malfunction, so declining to fire is the quieter
    // failure than telling the user nothing in a way that looks broken.
    if notification.title.trim().is_empty() || notification.body.trim().is_empty() {
        return;
    }
    let _ = app
        .notification()
        .builder()
        .title(&notification.title)
        .body(&notification.body)
        .show();
}
