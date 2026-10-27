//! Decision logic shared by the mem20controlz desktop shell.
//!
//! This crate exists so the parts of the shell that can be *wrong* are separate
//! from the parts that can only be *glued*. It has no Tauri types, no async
//! runtime and no TLS: every module here is exercised by `cargo test` on a
//! machine with no WebView, no display and no network.
//!
//! The rule the shell is built around: **a surface that answered is not
//! necessarily a surface that is well.** `/api/health` on the control plane
//! hard-codes `"ok"`, so it can prove liveness and nothing else.
//!
//! Modules:
//! - [`tray`]  -- fleet aggregate glyph state and notification decisions (#37)
//! - [`poller`] -- which route to poll, and what a failure may be called (#37)
//!
//! NOTE for the merge with #36: that branch declares `health`, `http` and
//! `sidecar` here. When both land, this list becomes the union of the two; the
//! `tray` and `poller` modules themselves depend on nothing from those.

pub mod poller;
pub mod tray;

pub use poller::{classify, path_for, tick, PollResult, Tick, POLL_INTERVAL_MS};
pub use tray::{
    aggregate_fleet_health, format_age, is_stale, FleetHealth, Notification, NotificationEngine,
    Panel, RegistryPayload, Suppressed, SuppressionCounts, CONFIRMATIONS_REQUIRED, STALE_AFTER_S,
};

/// The unauthenticated liveness route. The only route the shell may call before
/// a session exists (#37, AC-37-15).
pub const HEALTH_PATH: &str = "/api/health";

/// The authenticated fleet route.
pub const REGISTRY_PATH: &str = "/api/registry";
