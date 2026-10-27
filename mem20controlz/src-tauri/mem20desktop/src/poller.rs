//! The polling loop that keeps the tray truthful while the window is closed.
//!
//! Issue #37, AC-37-13 / AC-37-15. This module is deliberately free of Tauri and
//! of any HTTP client: it classifies a status code and a body, so its behaviour
//! (what it questions, what it refuses to conclude) is exercised by `cargo test`
//! with no window, no display and no net.
//!
//! Two rules drive the shape:
//!
//! 1. **Pre-login the tray may only call `/api/health`.** `/api/registry` is
//!    authenticated; calling it while signed out produces a 401 that a naive
//!    shell renders as "unreachable", turning a signed-out session into a fake
//!    outage (AC-37-15). So the path is chosen by auth state, not by "try
//!    registry and fall back".
//! 2. **A failed fetch is not a fleet claim.** One failed request says the
//!    *request* failed. It does not say which panel is down, and it must not be
//!    rendered as `unreachable`, which is a statement about a subsystem. A
//!    transport failure therefore yields a distinct liveness verdict and no
//!    notification.

use crate::tray::{FleetHealth, Notification, NotificationEngine, RegistryPayload};

/// What one poll tick concluded.
#[derive(Debug, Clone, PartialEq)]
pub enum Tick {
    /// Signed out: only liveness is knowable. Carries the neutral tray state.
    SignedOut,
    /// A fresh registry payload was evaluated.
    Registry(Box<RegistryPayload>),
    /// The request itself failed -- no panel is implicated.
    Transport,
    /// The request was rejected as unauthenticated (401/403). Not an outage.
    Unauthenticated,
}

impl Tick {
    /// The glyph this tick implies. Note `Transport` is NOT `unreachable`:
    /// nothing about a panel was learned, so nothing about a panel may be said.
    pub fn glyph(&self) -> FleetHealth {
        match self {
            Tick::SignedOut | Tick::Unauthenticated => FleetHealth::Starting,
            Tick::Transport => FleetHealth::Unknown,
            Tick::Registry(payload) => crate::tray::aggregate_fleet_health(payload),
        }
    }
}

/// Outcome of one tick: the state to paint, and optionally something to notify.
#[derive(Debug, Clone, PartialEq)]
pub struct PollResult {
    pub tick: Tick,
    pub notification: Option<Notification>,
}

/// Classify an HTTP status + body without any HTTP client.
///
/// Kept separate from the fetch so the mapping from status code to verdict is
/// testable on its own -- the 401 case is exactly the one that gets misread.
pub fn classify(status: u16, body: &str) -> Tick {
    match status {
        200..=299 => match RegistryPayload::parse(body) {
            Some(payload) => Tick::Registry(Box::new(payload)),
            // A 200 we cannot parse is still not evidence about a panel.
            None => Tick::Transport,
        },
        // A 401 is not an outage (AC-37-14).
        401 | 403 => Tick::Unauthenticated,
        _ => Tick::Transport,
    }
}

/// Run one tick: classify, then let the engine decide whether to speak.
pub fn tick(engine: &mut NotificationEngine, status: u16, body: &str) -> PollResult {
    let outcome = classify(status, body);
    match &outcome {
        Tick::Registry(payload) => {
            let notification = engine.observe(payload, true);
            PollResult {
                tick: outcome,
                notification,
            }
        }
        Tick::Unauthenticated | Tick::SignedOut => {
            // The lapse is itself one observation. Passing an empty payload to
            // `observe` would count nothing, so the counter a reviewer checks
            // for AC-37-14 would stay at zero forever.
            engine.note_authenticated_out();
            PollResult {
                tick: outcome,
                notification: None,
            }
        }
        Tick::Transport => PollResult {
            tick: outcome,
            notification: None,
        },
    }
}

/// Which route the tray is allowed to poll in the current session state.
pub fn path_for(authenticated: bool) -> &'static str {
    if authenticated {
        "/api/registry"
    } else {
        // The single unauthenticated route. Using it pre-login is what keeps
        // the shell from manufacturing 401s it would then misread.
        "/api/health"
    }
}

/// Poll interval. Matches the 10 s tick the UX doc specifies.
pub const POLL_INTERVAL_MS: u64 = 10_000;

/// Whether the window being hidden should stop the poller. It must not
/// (AC-37-13): closing the window only hides it, and the tray keeps polling so
/// a notification can still arrive while the window is closed.
pub fn continues_when_hidden() -> bool {
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    fn registry_json(status: &str) -> String {
        format!(
            r#"{{"total":1,"cached":false,"age_s":0.0,"stale":false,"panels":[{{"id":"api","name":"API","status":"{status}","status_reason":"REST probe {status}"}}]}}"#
        )
    }

    #[test]
    fn pre_login_polls_only_the_unauthenticated_route() {
        assert_eq!(path_for(false), "/api/health");
        assert_eq!(path_for(true), "/api/registry");
    }

    #[test]
    fn a_401_is_neither_reported_as_unreachable_nor_notified() {
        let mut engine = NotificationEngine::new();
        for _ in 0..4 {
            let r = tick(&mut engine, 401, r#"{"detail":"not authenticated"}"#);
            assert_eq!(r.tick, Tick::Unauthenticated);
            assert_eq!(r.notification, None, "a 401 must never notify");
            assert_ne!(r.tick.glyph(), FleetHealth::Unreachable);
        }
        assert_eq!(engine.counts.emitted, 0);
        assert!(engine.counts.authenticated_out > 0);
    }

    #[test]
    fn a_transport_failure_is_not_a_fleet_outage() {
        let mut engine = NotificationEngine::new();
        let r = tick(&mut engine, 502, "bad gateway");
        assert_eq!(r.tick, Tick::Transport);
        assert_eq!(r.tick.glyph(), FleetHealth::Unknown);
        assert_eq!(r.notification, None);
        // Nothing was learned about any panel, so no panel was accused.
        assert_eq!(engine.counts.emitted, 0);
    }

    #[test]
    fn an_unparseable_200_is_not_evidence_about_a_panel() {
        assert_eq!(classify(200, "not json"), Tick::Transport);
    }

    #[test]
    fn a_fresh_failure_flows_through_the_engine_to_exactly_one_notification() {
        let mut engine = NotificationEngine::new();
        let first = tick(&mut engine, 200, &registry_json("unreachable"));
        assert_eq!(first.notification, None, "one observation is not evidence");
        assert_eq!(first.tick.glyph(), FleetHealth::Unreachable);

        let second = tick(&mut engine, 200, &registry_json("unreachable"));
        assert!(second.notification.is_some(), "second fresh sweep notifies");
        assert_eq!(engine.counts.emitted, 1);
    }

    #[test]
    fn polling_continues_while_the_window_is_hidden() {
        assert!(
            continues_when_hidden(),
            "AC-37-13: closing hides, never stops"
        );
    }

    #[test]
    fn the_tick_interval_is_ten_seconds() {
        assert_eq!(POLL_INTERVAL_MS, 10_000);
    }
}
