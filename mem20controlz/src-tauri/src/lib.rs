//! Tauri 2 shell for the mem20controlz control plane.
//!
//! Issue #35: put the **existing** React bundle in a native window. No UI
//! rewrite -- `mem20controlz/static/` is loaded as-is.
//! Issue #36: own the backend. The shell reserves an ephemeral loopback port,
//! starts the FastAPI process, and reports ready only once it actually answers.
//!
//! Everything decision-shaped (identity check, status scoring, probe age,
//! timeouts, port reservation, restart policy) lives in the `mem20desktop`
//! crate next door, which has no Tauri dependency and is covered by
//! `cargo test`. This file is glue: register commands, open a window, hand back
//! verdicts.
//!
//! Still out of scope by design, and deliberately not stubbed into looking
//! finished: tray + notifications (#37), packaging/signing/update (#40).

use std::sync::Mutex;

use mem20desktop::sidecar::{self, Endpoint, LaunchSpec, SidecarState};
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
    /// Display text, e.g. "control plane up - 0.1.0 - uptime 12 s".
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

fn report_from(liveness: mem20desktop::ControlPlaneLiveness, url: String) -> ProbeReport {
    let assessment = mem20desktop::Assessment::new(liveness, 0.0);
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

/// The backend the shell owns (#36).
///
/// `endpoint` is kept even after the process exits so the UI can say which
/// address failed.
#[derive(Default)]
struct Backend {
    endpoint: Option<Endpoint>,
    child: Option<std::process::Child>,
    state: Option<SidecarState>,
}

/// Probe `GET /api/health` on the owned backend, falling back to the documented
/// service port when nothing has been started yet.
#[tauri::command]
fn probe_control_plane(port: Option<u16>, backend: tauri::State<'_, Mutex<Backend>>) -> ProbeReport {
    let owned = backend.lock().ok().and_then(|b| b.endpoint.clone());
    let endpoint = owned.unwrap_or_else(|| Endpoint {
        host: mem20desktop::DEFAULT_CONTROL_HOST.to_string(),
        port: port.unwrap_or(mem20desktop::DEFAULT_CONTROL_PORT),
    });

    let started = std::time::Instant::now();
    let liveness = sidecar::probe_port(&endpoint, mem20desktop::http::Limits::default());
    let mut report = report_from(liveness, endpoint.health_url());
    report.age_s = started.elapsed().as_secs_f64();
    report.stale = false;
    report
}

/// Reserve a port, start the backend, and return only once it answers.
///
/// Blocks for up to `sidecar::READY_BUDGET`, so the frontend must call this off
/// the UI thread. On failure the error string names what actually happened
/// (never ready / could not spawn), so the console can show a real reason.
#[tauri::command]
fn start_backend(backend: tauri::State<'_, Mutex<Backend>>) -> Result<String, String> {
    let (listener, endpoint) = sidecar::reserve_port().map_err(|e| e.to_string())?;
    let spec = LaunchSpec::python_module().with_port(&endpoint);

    // The listener is dropped just before spawn so the child can bind. The
    // window is small but unavoidable without passing the fd through.
    drop(listener);

    let child = spec.spawn().map_err(|e| e.to_string())?;
    let base = endpoint.base_url();

    {
        let mut guard = backend.lock().map_err(|_| "backend lock poisoned".to_string())?;
        guard.endpoint = Some(endpoint.clone());
        guard.child = Some(child);
        guard.state = Some(SidecarState::Starting {
            endpoint: endpoint.clone(),
            since: std::time::Instant::now(),
        });
    }

    match sidecar::wait_until_ready(
        &endpoint,
        sidecar::READY_BUDGET,
        sidecar::READY_POLL_INTERVAL,
    ) {
        Ok(_) => {
            let mut guard = backend.lock().map_err(|_| "backend lock poisoned".to_string())?;
            guard.state = Some(SidecarState::Ready {
                endpoint: endpoint.clone(),
            });
            Ok(base)
        }
        Err(err) => Err(err.to_string()),
    }
}

/// What the supervisor currently knows, without pretending to know more.
#[tauri::command]
fn backend_status(backend: tauri::State<'_, Mutex<Backend>>) -> String {
    let guard = match backend.lock() {
        Ok(g) => g,
        Err(_) => return "unknown (lock poisoned)".to_string(),
    };
    match (&guard.state, &guard.endpoint) {
        (Some(SidecarState::Ready { endpoint }), _) => {
            format!("ready on {}", endpoint.base_url())
        }
        (Some(SidecarState::Starting { endpoint, .. }), _) => {
            format!("starting on {}", endpoint.base_url())
        }
        (Some(SidecarState::Exited { gave_up, .. }), _) => {
            if *gave_up {
                "backend exited and the restart budget is spent".to_string()
            } else {
                "backend exited; a restart is pending".to_string()
            }
        }
        (_, Some(endpoint)) => format!("idle (last endpoint {})", endpoint.base_url()),
        (_, None) => "idle (no backend started)".to_string(),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(Mutex::new(Backend::default()))
        .invoke_handler(tauri::generate_handler![
            probe_control_plane,
            start_backend,
            backend_status
        ])
        .run(tauri::generate_context!())
        .expect("error while running the mem20controlz desktop shell");
}
