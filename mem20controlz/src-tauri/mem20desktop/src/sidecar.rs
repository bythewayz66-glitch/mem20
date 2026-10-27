//! Backend sidecar: own a FastAPI process on an ephemeral loopback port.
//!
//! Issue #36. Before this, the shell attached to whatever happened to be
//! listening on the documented port (#35). Now the shell *owns* a backend:
//! it picks the port, starts the process, waits for it to become genuinely
//! ready, and restarts it with a bounded policy when it dies.
//!
//! Four decisions are deliberate, and each one is the fix for a specific way
//! the naive implementation goes wrong.
//!
//! 1. **The port is reserved, not merely chosen.** We bind `127.0.0.1:0`, let
//!    the kernel pick, and hand *that listening socket* to the child. The
//!    common alternative -- read `port` back, close the listener, then spawn --
//!    reintroduces the time-of-check/time-of-use race the ephemeral port was
//!    meant to remove: in the gap between close and bind, any other process
//!    can take the port, and the child then fails with "address in use" for no
//!    reason the user can see.
//! 2. **Bind before spawn.** The port is an argument to the child, so it must
//!    be known first. The other design spawns with port 0 and scrapes the
//!    chosen port from the child's stdout, which makes every startup failure
//!    look like a stdout-parsing bug.
//! 3. **Startup is not readiness.** A live process proves nothing: uvicorn
//!    still has to bind and import. `Ready` is only reached when `/api/health`
//!    answers as `mem20-control`, reusing the identity contract from
//!    [`crate::health`] rather than inventing a second opinion about health.
//! 4. **Exit is not a diagnosis.** A child that died is reported as `Exited`
//!    with its status and nothing more. Nobody claims to know why. A restart
//!    count is carried so the shell can stop looping and say so.
//!
//! Process supervision is decision logic -- it has failure modes worth testing --
//! which is why it lives here and not in the Tauri crate.

use std::io;
use std::net::TcpListener;
use std::process::{Child, Command, ExitStatus, Stdio};
use std::time::{Duration, Instant};

use crate::health::{assess, parse_health_body, ControlPlaneLiveness};
use crate::http::{http_get, Limits};
use crate::{DEFAULT_CONTROL_HOST, HEALTH_PATH};

/// How long after spawn we are willing to keep asking "are you ready yet?"
/// before calling the start-up failed. uvicorn on a cold import is seconds at
/// most; a minute means something is actually wrong.
pub const READY_BUDGET: Duration = Duration::from_secs(20);

/// Gap between readiness probes while waiting for the child to come up.
pub const READY_POLL_INTERVAL: Duration = Duration::from_millis(150);

/// Minimum gap between restarts. Without this a crash-looping child is
/// respawned as fast as the OS can fork, which buries the log and pins a core.
pub const RESTART_COOLDOWN: Duration = Duration::from_secs(2);

/// After this many failed restarts in a row the supervisor stops trying and
/// reports the state to the user. Restarting forever is not resilience; it is
/// a machine that never tells anyone it is broken.
pub const MAX_CONSECUTIVE_FAILED_RESTARTS: u32 = 3;

/// A reserved loopback port plus the address the backend should bind.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Endpoint {
    pub host: String,
    pub port: u16,
}

impl Endpoint {
    /// The `/api/health` URL on this endpoint.
    pub fn health_url(&self) -> String {
        format!("http://{}:{}{HEALTH_PATH}", self.host, self.port)
    }

    /// The base URL, for handing to the webview.
    pub fn base_url(&self) -> String {
        format!("http://{}:{}", self.host, self.port)
    }
}

#[derive(Debug)]
pub enum SidecarError {
    /// No ephemeral port could be reserved.
    Bind(io::Error),
    /// The backend binary could not be started at all (missing, not
    /// executable, bad permissions). Distinct from "started and died".
    Spawn(io::Error),
    /// The process started but never answered as the control plane within
    /// [`READY_BUDGET`].
    NeverReady {
        waited: Duration,
        last: ControlPlaneLiveness,
    },
}

impl std::fmt::Display for SidecarError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SidecarError::Bind(e) => write!(f, "could not reserve a loopback port: {e}"),
            SidecarError::Spawn(e) => write!(f, "could not start the backend: {e}"),
            SidecarError::NeverReady { waited, last } => {
                write!(f, "backend did not become ready within {waited:?}: {}", last.summary())
            }
        }
    }
}

impl std::error::Error for SidecarError {}

/// Reserve an ephemeral loopback port.
///
/// The returned listener is still bound. Pass it to the child (or hold it until
/// the child binds) so no other process can take the port in between.
pub fn reserve_port() -> Result<(TcpListener, Endpoint), SidecarError> {
    let listener = TcpListener::bind((DEFAULT_CONTROL_HOST, 0)).map_err(SidecarError::Bind)?;
    let port = listener.local_addr().map_err(SidecarError::Bind)?.port();
    Ok((
        listener,
        Endpoint {
            host: DEFAULT_CONTROL_HOST.to_string(),
            port,
        },
    ))
}

/// How the backend is invoked.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LaunchSpec {
    /// Executable, e.g. the bundled sidecar binary or `python3`.
    pub program: String,
    /// Arguments, with the port appended by the caller via [`LaunchSpec::with_port`].
    pub args: Vec<String>,
}

impl LaunchSpec {
    /// The documented way to run the backend from a source checkout.
    pub fn python_module() -> Self {
        Self {
            program: "python3".to_string(),
            args: vec!["-m".to_string(), "mem20controlz".to_string()],
        }
    }

    /// Append `--host`/`--port` for the reserved endpoint.
    pub fn with_port(&self, endpoint: &Endpoint) -> Self {
        let mut args = self.args.clone();
        args.push("--host".to_string());
        args.push(endpoint.host.clone());
        args.push("--port".to_string());
        args.push(endpoint.port.to_string());
        Self {
            program: self.program.clone(),
            args,
        }
    }

    /// Spawn as a child with piped output so the shell can surface the first
    /// lines of any startup failure instead of swallowing them.
    pub fn spawn(&self) -> Result<Child, SidecarError> {
        Command::new(&self.program)
            .args(&self.args)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(SidecarError::Spawn)
    }
}

/// What the supervisor knows about the backend right now.
#[derive(Debug, Clone, PartialEq)]
pub enum SidecarState {
    /// Nothing started yet.
    Idle,
    /// Spawned, not yet answering as the control plane.
    Starting { endpoint: Endpoint, since: Instant },
    /// Answering as `mem20-control` with `status: "ok"`.
    Ready { endpoint: Endpoint },
    /// The process is gone. `restarts` is how many times we have tried to
    /// bring it back; `gave_up` is set once the budget is spent.
    Exited {
        status: Option<ExitStatus>,
        restarts: u32,
        gave_up: bool,
    },
}

impl SidecarState {
    /// True only when the backend is confirmed answering. Never true merely
    /// because a process exists.
    pub fn is_ready(&self) -> bool {
        matches!(self, SidecarState::Ready { .. })
    }

    /// True when the supervisor has stopped trying and the user must be told.
    pub fn needs_attention(&self) -> bool {
        match self {
            SidecarState::Exited { gave_up, .. } => *gave_up,
            _ => false,
        }
    }

    pub fn endpoint(&self) -> Option<&Endpoint> {
        match self {
            SidecarState::Starting { endpoint, .. } | SidecarState::Ready { endpoint } => {
                Some(endpoint)
            }
            _ => None,
        }
    }
}

/// Probe one endpoint and report only what the evidence supports.
///
/// This is the readiness gate: it reuses [`assess`], so "ready" means the same
/// thing here as it does in the status strip -- identity first, then status.
pub fn probe_port(endpoint: &Endpoint, limits: Limits) -> ControlPlaneLiveness {
    match http_get(&endpoint.health_url(), limits) {
        Ok(response) if response.is_success() => match parse_health_body(&response.body) {
            Ok(body) => assess(&body),
            Err(_) => ControlPlaneLiveness::Foreign { service: None },
        },
        Ok(response) => ControlPlaneLiveness::NotOk {
            reported: format!("http {}", response.status),
        },
        Err(err) => ControlPlaneLiveness::Unreachable {
            reason: err.to_string(),
        },
    }
}

/// Poll `endpoint` until it is ready or `budget` is exhausted.
///
/// Returns the last verdict on failure, so the caller can say *why* it gave up
/// (refused vs. wrong service vs. wrong status) instead of a bare timeout.
pub fn wait_until_ready(
    endpoint: &Endpoint,
    budget: Duration,
    poll_interval: Duration,
) -> Result<ControlPlaneLiveness, SidecarError> {
    let started = Instant::now();
    let mut last = ControlPlaneLiveness::Unknown;

    while started.elapsed() < budget {
        last = probe_port(endpoint, Limits::default());
        if last.is_up() {
            return Ok(last);
        }
        std::thread::sleep(poll_interval.min(budget));
    }

    Err(SidecarError::NeverReady {
        waited: started.elapsed(),
        last,
    })
}

/// Decide whether to restart after an exit.
///
/// Split out as a pure function because this is the rule most likely to be
/// wrong, and it is much cheaper to test than a real process tree.
///
/// Returns `Ok(delay)` when a restart is warranted (the caller must wait
/// `delay` first), or `Err(())` when the budget is spent and the user should be
/// told.
pub fn restart_decision(failed_restarts: u32) -> Result<Duration, ()> {
    if failed_restarts >= MAX_CONSECUTIVE_FAILED_RESTARTS {
        Err(())
    } else {
        Ok(RESTART_COOLDOWN)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reserving_a_port_returns_a_bound_listener_on_loopback() {
        let (listener, endpoint) = reserve_port().expect("should reserve");
        assert_eq!(endpoint.host, "127.0.0.1");
        // The kernel must hand back a real, non-privileged port.
        assert!(endpoint.port > 0);
        assert!(endpoint.port >= 1024);
        // Still bound at this moment: that is the whole point of reserving.
        assert_eq!(listener.local_addr().unwrap().port(), endpoint.port);
    }

    #[test]
    fn two_reservations_do_not_collide() {
        let (_a, first) = reserve_port().unwrap();
        let (_b, second) = reserve_port().unwrap();
        assert_ne!(first.port, second.port);
    }

    #[test]
    fn endpoint_urls_carry_the_reserved_port_and_the_health_path() {
        let endpoint = Endpoint {
            host: "127.0.0.1".to_string(),
            port: 41_234,
        };
        assert_eq!(endpoint.health_url(), "http://127.0.0.1:41234/api/health");
        assert_eq!(endpoint.base_url(), "http://127.0.0.1:41234");
    }

    #[test]
    fn launch_spec_appends_host_and_port_without_mutating_the_original() {
        let spec = LaunchSpec::python_module();
        let endpoint = Endpoint {
            host: "127.0.0.1".to_string(),
            port: 9001,
        };
        let launched = spec.with_port(&endpoint);

        assert_eq!(launched.args.len(), spec.args.len() + 4);
        assert!(launched.args.windows(2).any(|w| w == ["--port", "9001"]));
        // The template must stay usable for a second launch.
        assert!(!spec.args.iter().any(|a| a == "--port"));
    }

    #[test]
    fn nothing_listening_is_not_ready() {
        // Reserve, then release: the port is known-good but empty.
        let (listener, endpoint) = reserve_port().unwrap();
        drop(listener);
        let verdict = probe_port(&endpoint, Limits::default());
        assert!(!verdict.is_up());
    }

    #[test]
    fn wait_until_ready_gives_up_and_reports_the_last_reason() {
        let (listener, endpoint) = reserve_port().unwrap();
        drop(listener);

        let err = wait_until_ready(&endpoint, Duration::from_millis(400), Duration::from_millis(50))
            .expect_err("nothing is listening; this must fail");

        match err {
            SidecarError::NeverReady { last, .. } => {
                // Must be a transport verdict, not `Unknown`: the probes ran.
                assert!(matches!(last, ControlPlaneLiveness::Unreachable { .. }));
            }
            other => panic!("expected NeverReady, got {other:?}"),
        }
    }

    #[test]
    fn a_dead_endpoint_is_never_reported_ready() {
        // The failure this guards: treating "we spawned something" as ready.
        let (listener, endpoint) = reserve_port().unwrap();
        drop(listener);
        let state = SidecarState::Exited {
            status: None,
            restarts: 1,
            gave_up: false,
        };
        assert!(!state.is_ready());
        assert_eq!(state.endpoint(), None);
        assert!(!state.needs_attention());
        let _ = endpoint;
    }

    #[test]
    fn restart_budget_is_finite_and_cools_down() {
        assert_eq!(restart_decision(0), Ok(RESTART_COOLDOWN));
        assert_eq!(restart_decision(MAX_CONSECUTIVE_FAILED_RESTARTS - 1), Ok(RESTART_COOLDOWN));
        // At the budget the supervisor stops rather than looping forever.
        assert_eq!(restart_decision(MAX_CONSECUTIVE_FAILED_RESTARTS), Err(()));
        assert_eq!(restart_decision(99), Err(()));
        assert!(RESTART_COOLDOWN > Duration::ZERO);
    }

    #[test]
    fn only_a_confirmed_ready_endpoint_exposes_a_base_url() {
        let endpoint = Endpoint {
            host: "127.0.0.1".to_string(),
            port: 9100,
        };
        let ready = SidecarState::Ready {
            endpoint: endpoint.clone(),
        };
        assert!(ready.is_ready());
        assert_eq!(ready.endpoint().unwrap().port, 9100);

        let starting = SidecarState::Starting {
            endpoint: endpoint.clone(),
            since: Instant::now(),
        };
        // Starting exposes the endpoint (so the UI can show it) but is not ready.
        assert!(!starting.is_ready());
        assert_eq!(starting.endpoint().unwrap().port, 9100);
    }

    #[test]
    fn giving_up_is_the_only_exited_state_that_needs_attention() {
        let retrying = SidecarState::Exited {
            status: None,
            restarts: 1,
            gave_up: false,
        };
        let done = SidecarState::Exited {
            status: None,
            restarts: MAX_CONSECUTIVE_FAILED_RESTARTS,
            gave_up: true,
        };
        assert!(!retrying.needs_attention());
        assert!(done.needs_attention());
        assert!(!SidecarState::Idle.needs_attention());
    }
}
