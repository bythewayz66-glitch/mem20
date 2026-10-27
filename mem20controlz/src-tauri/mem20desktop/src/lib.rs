//! Decision logic shared by the mem20controlz desktop shell.
//!
//! This crate exists so the parts of the shell that can be *wrong* are
//! separate from the parts that can only be *glued*. It has no Tauri types, no
//! async runtime and no TLS: every module here is exercised by `cargo test`
//! on a machine with no WebView, no display and no network.
//!
//! The rule the shell is built around: **a surface that answered is not
//! necessarily a surface that is well.** `/api/health` on the control plane
//! hard-codes `"ok"`, so it can prove liveness and nothing else. Types here
//! refuse to describe more than the evidence supports.

pub mod health;
pub mod http;
pub mod sidecar;

pub use health::{
    assess, parse_health_body, Assessment, ControlPlaneLiveness, HealthBody, HealthError,
    CONTROL_PLANE_SERVICE,
};
pub use http::{http_get, HttpError, Response};
pub use sidecar::{Endpoint, LaunchSpec, SidecarError, SidecarState};

/// Where a locally installed control plane listens by default.
///
/// The systemd unit and `mem20controlz/README.md` both document `8890`; the
/// shell uses the same number so a desktop launch and a service launch are
/// describing the same thing.
///
/// Since #36 the sidecar prefers an ephemeral port and this is only the
/// fallback for attaching to an already-running service.
pub const DEFAULT_CONTROL_HOST: &str = "127.0.0.1";
pub const DEFAULT_CONTROL_PORT: u16 = 8890;

/// The unauthenticated liveness route. The only route the shell may call
/// before a session exists.
pub const HEALTH_PATH: &str = "/api/health";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_probe_target_matches_the_documented_service_port() {
        // Guards against the shell silently inventing its own port and then
        // reporting "down" against a service that is running perfectly.
        assert_eq!(DEFAULT_CONTROL_PORT, 8890);
        assert_eq!(DEFAULT_CONTROL_HOST, "127.0.0.1");
        assert_eq!(HEALTH_PATH, "/api/health");
    }
}
