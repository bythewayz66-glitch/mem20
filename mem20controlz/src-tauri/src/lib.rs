//! Tauri 2 shell for the mem20controlz control plane.
//!
//! Scope of issue #35: put the **existing** React bundle in a native window.
//! No UI rewrite — `mem20controlz/static/` is loaded as-is.
//!
//! Everything decision-shaped (identity check, status scoring, probe age,
//! timeouts) lives in the `mem20desktop` crate next door, which has no Tauri
//! dependency and is covered by `cargo test`. This file is glue: register a
//! command, open the window, hand back the verdict.
//!
//! Out of scope by design, and deliberately not stubbed into looking finished:
//! spawning the backend (issue #36), tray + notifications (issue #37),
//! packaging/signing/update (issue #40).

use serde::Serialize;

/// What the shell tells the frontend about the control plane.
///
/// `summary` is pre-rendered in Rust so the one-line text and the structured
/// verdict cannot drift apart between the status strip and a future tray
/// tooltip.
#[derive(Debug, Clone, Serialize)]
pub struct ProbeReport {
    /// Machine-readable verdict: `unknown` | `starting` | `up` | `not-ok` |
    /// `foreign` | `unreachable`.
    pub state: &'static str,
    /// True only when the peer identified as `mem20-control` *and* said `ok`.
    pub up: bool,
    /// True when there is an evidenced problem worth surfacing.
    pub needs_attention: bool,
    /// How old the evidence is. Always present so a cached reading can never
    /// be presented as a live one.
    pub age_s: f64,
    pub stale: bool,
    /// Display text, e.g. "control plane up · 0.1.0 · uptime 12 s".
    pub summary: String,
    /// The exact URL probed, so a support conversation starts from facts.
    pub probed_url: String,
}

fn state_name(liveness: &mem20desktop::ControlPlaneLiveness) -> &'static str {
    use mem20desktop::ControlPlaneLiveness as L;
    match liveness {
        L::Unknown => "unknown",
        L::Starting => "starting",
        L::Up { .. } => "up",
        L::NotOk { .. } => "not-ok",
        L::Foreign { .. } => "foreign",
        L::Unreachable { .. } => "unreachable",
    }
}

/// Probe `GET /api/health` and report what the evidence actually supports.
///
/// The frontend calls this from the status strip. `port` defaults to the
/// documented service port (`8890`); it is a parameter rather than hard-coded
/// so a future ephemeral-port sidecar (#36) can pass the resolved port in
/// without touching this function.
#[tauri::command]
fn probe_control_plane(port: Option<u16>) -> ProbeReport {
    let port = port.unwrap_or(mem20desktop::DEFAULT_CONTROL_PORT);
    let url = format!(
        "http://{}:{}{}",
        mem20desktop::DEFAULT_CONTROL_HOST,
        port,
        mem20desktop::HEALTH_PATH
    );

    let started = std::time::Instant::now();
    let liveness = match mem20desktop::http_get(&url, mem20desktop::http::Limits::default()) {
        Ok(response) if response.is_success() => match mem20desktop::parse_health_body(&response.body)
        {
            Ok(body) => mem20desktop::assess(&body),
            // A well-formed HTTP answer whose body is not a health body is
            // more likely a misrouted peer than a broken control plane.
            Err(_) => mem20desktop::ControlPlaneLiveness::Foreign { service: None },
        },
        Ok(response) => mem20desktop::ControlPlaneLiveness::NotOk {
            reported: format!("http {}", response.status),
        },
        Err(err) => mem20desktop::ControlPlaneLiveness::Unreachable {
            reason: err.to_string(),
        },
    };

    let assessment = mem20desktop::Assessment::new(liveness, started.elapsed().as_secs_f64());

    ProbeReport {
        state: state_name(&assessment.liveness),
        up: assessment.liveness.is_up(),
        needs_attention: assessment.liveness.needs_attention(),
        age_s: assessment.age_s,
        stale: assessment.is_stale(),
        summary: assessment.summary(),
        probed_url: url,
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![probe_control_plane])
        .run(tauri::generate_context!())
        .expect("error while running the mem20controlz desktop shell");
}
