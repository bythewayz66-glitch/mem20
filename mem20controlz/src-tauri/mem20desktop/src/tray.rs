//! Fleet aggregation and notification decisions for the system tray.
//!
//! Issue #37. The tray icon itself is trivial; this module is the part that can
//! produce a false alarm, so it is a pure function set with no Tauri types and
//! no clock -- the caller injects time and payloads.
//!
//! Contract: `GET /api/registry` ->
//! `{ panels[], counts{}, total, cached, age_s, stale, sweeping?, ... }`
//! with `panels[i].status` in `{ok, degraded, unreachable, no-health, unknown}`.
//! No backend change is required by this issue.
//!
//! The single rule the whole module serves: **a tray that alerts on cached or
//! stale data is worse than no tray**, because it manufactures outages out of
//! its own polling cache. Every suppression below exists for that.

use serde_json::Value;

/// Aggregate fleet verdict shown by the tray glyph.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FleetHealth {
    /// A concurrent sweep is in flight; the backend has no panels yet.
    Starting,
    Unreachable,
    Degraded,
    /// A panel could not be confirmed. Never silently green.
    Unknown,
    /// A probe gap, not a fault.
    NoHealth,
    /// Verified: at least one panel, all ok.
    Ok,
}

impl FleetHealth {
    pub fn as_str(self) -> &'static str {
        match self {
            FleetHealth::Starting => "starting",
            FleetHealth::Unreachable => "unreachable",
            FleetHealth::Degraded => "degraded",
            FleetHealth::Unknown => "unknown",
            FleetHealth::NoHealth => "no-health",
            FleetHealth::Ok => "ok",
        }
    }

    /// Accessible name for the tray item (AC-37-12). State is carried by shape
    /// AND this name, never by hue alone, so a user with no colour perception
    /// can still read the fleet state.
    pub fn accessible_name(self) -> &'static str {
        match self {
            FleetHealth::Starting => "Fleet: starting",
            FleetHealth::Unreachable => "Fleet: unreachable",
            FleetHealth::Degraded => "Fleet: degraded",
            FleetHealth::Unknown => "Fleet: unknown",
            FleetHealth::NoHealth => "Fleet: no health check",
            FleetHealth::Ok => "Fleet: ok",
        }
    }

    /// The tray tooltip for this state.
    ///
    /// Leads with the **probe age**, not with "last refresh succeeded". Those
    /// two numbers differ by the cache age, and showing the refresh clock is
    /// how a 40-second-old reading gets read as live (AC-37-04). When the
    /// reading is stale the tooltip says so, because a user who never opens the
    /// window has only this text to go on.
    pub fn tooltip(self, age_s: f64, stale: bool) -> String {
        let state = self.accessible_name();
        // A negative or non-finite age is not a measurement, so it is not shown.
        if !age_s.is_finite() || age_s < 0.0 {
            return state.to_string();
        }
        let age = format_age(age_s);
        if stale {
            format!("{state} - last probed {age} ago (stale)")
        } else {
            format!("{state} - probed {age} ago")
        }
    }

    /// Only these two are worth a native notification (README 1.3 AC-V3).
    /// `no-health` is a probe gap and `unknown` is an unconfirmed reading;
    /// notifying on either would accuse a subsystem on absent evidence.
    pub fn is_notification_worthy(self) -> bool {
        matches!(self, FleetHealth::Unreachable | FleetHealth::Degraded)
    }
}

/// One panel out of `/api/registry`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Panel {
    pub id: String,
    pub name: String,
    /// Raw status string. Kept as text so an unrecognised value from a newer
    /// backend degrades to `unknown` instead of failing the parse.
    pub status: String,
    /// The backend's own explanation. Used verbatim in notification copy.
    pub status_reason: Option<String>,
}

/// The parsed `/api/registry` payload. Only the fields this issue consumes.
#[derive(Debug, Clone, PartialEq)]
pub struct RegistryPayload {
    pub panels: Vec<Panel>,
    pub total: u64,
    /// True when the backend served this from its cache rather than a fresh sweep.
    pub cached: bool,
    /// Cache age in seconds as reported by the backend.
    pub age_s: f64,
    pub stale: bool,
    /// Present and true only on the cold-start concurrent-sweep path.
    pub sweeping: bool,
}

impl RegistryPayload {
    /// Parse leniently: a malformed panel is skipped rather than failing the
    /// whole payload, because losing the fleet view over one bad record is
    /// worse than rendering the rest.
    pub fn parse(raw: &str) -> Option<Self> {
        let value: Value = serde_json::from_str(raw).ok()?;
        let object = value.as_object()?;

        let panels: Vec<Panel> = object
            .get("panels")
            .and_then(Value::as_array)
            .map(|items| {
                items
                    .iter()
                    .filter_map(|item| {
                        let panel = item.as_object()?;
                        Some(Panel {
                            id: panel.get("id").and_then(Value::as_str)?.to_string(),
                            name: panel
                                .get("name")
                                .and_then(Value::as_str)
                                .unwrap_or("unnamed")
                                .to_string(),
                            status: panel
                                .get("status")
                                .and_then(Value::as_str)
                                .unwrap_or("unknown")
                                .to_string(),
                            status_reason: panel
                                .get("status_reason")
                                .and_then(Value::as_str)
                                .map(str::to_string),
                        })
                    })
                    .collect()
            })
            .unwrap_or_default();

        Some(Self {
            total: object
                .get("total")
                .and_then(Value::as_u64)
                .unwrap_or(panels.len() as u64),
            cached: object.get("cached").and_then(Value::as_bool).unwrap_or(false),
            age_s: object
                .get("age_s")
                .and_then(Value::as_f64)
                .filter(|v| v.is_finite() && *v >= 0.0)
                .unwrap_or(0.0),
            stale: object.get("stale").and_then(Value::as_bool).unwrap_or(false),
            sweeping: object
                .get("sweeping")
                .and_then(Value::as_bool)
                .unwrap_or(false),
            panels,
        })
    }
}

/// A reading older than this is presented as stale (matches the UX doc).
pub const STALE_AFTER_S: f64 = 45.0;

/// A reading is stale if the backend says so, or if its own age says so.
///
/// Both are checked on purpose: `stale` is the backend's opinion and `age_s` is
/// the measurement, and trusting only one of them lets a backend that forgets
/// to set the flag publish an hours-old reading as live.
pub fn is_stale(payload: &RegistryPayload) -> bool {
    payload.stale || payload.age_s > STALE_AFTER_S
}

/// The aggregate glyph verdict. First match wins, in the documented order.
pub fn aggregate_fleet_health(payload: &RegistryPayload) -> FleetHealth {
    // 1. Only honest "wait" signal available.
    if payload.sweeping {
        return FleetHealth::Starting;
    }

    let has = |want: &str| payload.panels.iter().any(|p| p.status == want);

    if has("unreachable") {
        FleetHealth::Unreachable
    } else if has("degraded") {
        FleetHealth::Degraded
    } else if has("unknown") {
        FleetHealth::Unknown
    } else if has("no-health") {
        // Ranked last among non-ok: a probe gap must never masquerade as an outage.
        FleetHealth::NoHealth
    } else if payload.total > 0
        && !payload.panels.is_empty()
        && payload.panels.iter().all(|p| p.status == "ok")
    {
        FleetHealth::Ok
    } else {
        // Never ok by absence of evidence (AC-V1).
        FleetHealth::Unknown
    }
}

/// Human-readable age, always with a unit and never rounding a real age to
/// zero. `age_s` is the backend's own figure, so it is quoted rather than
/// recomputed from a local clock (AC-37-04).
pub fn format_age(age_s: f64) -> String {
    let seconds = age_s.max(0.0);
    if seconds < 60.0 {
        // At least "1 s": reporting a real 0.4 s reading as "0 s ago" makes a
        // fresh probe look like it never ran.
        format!("{} s", seconds.round().max(1.0) as u64)
    } else if seconds < 3600.0 {
        format!("{} min", (seconds / 60.0).round().max(1.0) as u64)
    } else {
        format!("{} h", (seconds / 3600.0).round().max(1.0) as u64)
    }
}

/// Why an observation did not produce a notification.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Suppressed {
    /// Same panel, same status, already notified for this transition.
    Unchanged,
    /// The sweep was served from cache; not evidence.
    Cached,
    /// The reading is stale; never alert on it.
    Stale,
    /// Signed out: a 401 is not an outage.
    AuthenticatedOut,
    /// The user muted notifications.
    Muted,
}

impl Suppressed {
    pub fn as_str(self) -> &'static str {
        match self {
            Suppressed::Unchanged => "unchanged",
            Suppressed::Cached => "cached",
            Suppressed::Stale => "stale",
            Suppressed::AuthenticatedOut => "authenticated_out",
            Suppressed::Muted => "muted",
        }
    }
}

/// Suppression counters, so every observation is accounted for (AC-37-09).
///
/// `emitted` counts *notifications*; `panels_emitted` counts the panels those
/// notifications covered. Keeping both is what makes the identity checkable:
/// every panel observation ends up either in `panels_emitted` or in exactly one
/// suppression bucket. An uncounted observation is how a "we never alert" bug
/// hides, so the identity is asserted rather than assumed.
#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct SuppressionCounts {
    pub unchanged: u32,
    pub cached: u32,
    pub stale: u32,
    pub authenticated_out: u32,
    pub muted: u32,
    /// Notifications raised (a coalesced toast counts once).
    pub emitted: u32,
    /// Panel observations covered by those notifications.
    pub panels_emitted: u32,
    /// A notification-worthy panel seen fewer than CONFIRMATIONS_REQUIRED
    /// times. Not a suppression for a *reason* -- it is simply not yet
    /// evidence -- so it gets its own named bucket rather than vanishing.
    pub pending_confirmation: u32,
    /// Panels whose status is not notification-worthy at all (`ok`,
    /// `no-health`, `unknown`). Out of scope by design, counted so that
    /// "out of scope" can never be confused with "silently dropped".
    pub not_worthy: u32,
}

impl SuppressionCounts {
    pub fn record(&mut self, s: Suppressed) {
        match s {
            Suppressed::Unchanged => self.unchanged += 1,
            Suppressed::Cached => self.cached += 1,
            Suppressed::Stale => self.stale += 1,
            Suppressed::AuthenticatedOut => self.authenticated_out += 1,
            Suppressed::Muted => self.muted += 1,
        }
    }

    pub fn suppressed_total(&self) -> u32 {
        self.unchanged + self.cached + self.stale + self.authenticated_out + self.muted
    }

    /// Every panel observation was either notified, suppressed for one of the
    /// five documented reasons, still awaiting confirmation, or not worthy of a
    /// notification in the first place. Nothing is silently dropped.
    ///
    /// The last two buckets are not "suppressions" in the README's sense -- the
    /// five reasons stay exactly as specified -- but they must still be counted,
    /// because an uncounted observation is indistinguishable from a bug that
    /// never fires.
    pub fn is_accounted(&self, panel_observations: u32) -> bool {
        self.panels_emitted
            + self.suppressed_total()
            + self.pending_confirmation
            + self.not_worthy
            == panel_observations
    }
}

/// A notification the shell should raise.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Notification {
    pub title: String,
    pub body: String,
    /// Panel ids this notification covers (at most 3 named, by design).
    pub panel_ids: Vec<String>,
}

/// Per-panel confirmation and dedupe state.
#[derive(Debug, Default, Clone)]
pub struct NotificationEngine {
    /// panel_id -> consecutive fresh sweeps reporting the same non-ok status.
    confirmations: std::collections::HashMap<String, (String, u32)>,
    /// panel_id -> (status, transition_seq) already notified.
    notified: std::collections::HashMap<String, (String, u64)>,
    /// panel_id -> the transition sequence currently in force.
    epochs: std::collections::HashMap<String, u64>,
    /// panel_id -> status seen on the previous fresh sweep. Used to detect a
    /// transition, including recovery to `ok`, which must re-arm the panel.
    last_status: std::collections::HashMap<String, String>,
    transition_seq: u64,
    pub muted: bool,
    pub counts: SuppressionCounts,
}

/// Fresh sweeps required before notifying. Two, not one: a single fresh
/// failure can be a transient probe blip, and the cost of a false alarm is the
/// user learning to ignore the tray.
pub const CONFIRMATIONS_REQUIRED: u32 = 2;

impl NotificationEngine {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn set_muted(&mut self, muted: bool) {
        self.muted = muted;
    }

    /// Feed one `/api/registry` payload; returns at most one coalesced
    /// notification (AC-37-08).
    pub fn observe(
        &mut self,
        payload: &RegistryPayload,
        authenticated: bool,
    ) -> Option<Notification> {
        let observations = payload.panels.len() as u32;

        // Pre-login: /api/registry is not ours to call, and a 401 is not an
        // outage (AC-37-14). Nothing is evaluated, nothing is accused.
        if !authenticated {
            self.counts.authenticated_out += observations;
            return None;
        }

        // Muted: the glyph still updates, alerts do not (AC-37-11).
        if self.muted {
            self.counts.muted += observations;
            return None;
        }

        // A stale or cached sweep is not evidence. Both suppress before any
        // confirmation counter moves, so a frozen refresher can never drift
        // into an alarm (AC-37-05, AC-37-06).
        if is_stale(payload) {
            self.counts.stale += observations;
            return None;
        }
        if payload.cached {
            self.counts.cached += observations;
            return None;
        }

        let mut candidates: Vec<&Panel> = Vec::new();

        for panel in &payload.panels {
            let previous = self.last_status.get(&panel.id).cloned();
            let changed = previous.as_deref() != Some(panel.status.as_str());

            if changed {
                // Any status change is a new transition -- including recovery
                // to `ok`, which must re-arm the panel so a later re-failure is
                // counted as new rather than deduped against the old toast.
                self.transition_seq += 1;
                let seq = self.transition_seq;
                self.epochs.insert(panel.id.clone(), seq);
                self.last_status
                    .insert(panel.id.clone(), panel.status.clone());
                self.confirmations
                    .insert(panel.id.clone(), (panel.status.clone(), 1));
                self.notified.remove(&panel.id);
            } else {
                let entry = self
                    .confirmations
                    .entry(panel.id.clone())
                    .or_insert_with(|| (panel.status.clone(), 0));
                entry.1 += 1;
            }

            let health = status_to_health(&panel.status);
            if !health.is_notification_worthy() {
                self.counts.not_worthy += 1;
                // ok / no-health / unknown: never notify. `no-health` is a probe
                // gap and `unknown` is an unconfirmed reading; accusing on
                // either is the false alarm this module exists to prevent.
                continue;
            }

            let confirmations = self
                .confirmations
                .get(&panel.id)
                .map(|(_, n)| *n)
                .unwrap_or(0);
            if confirmations < CONFIRMATIONS_REQUIRED {
                self.counts.pending_confirmation += 1;
                continue;
            }

            let epoch = *self.epochs.get(&panel.id).unwrap_or(&0);
            if let Some((status, seq)) = self.notified.get(&panel.id) {
                if status == &panel.status && *seq == epoch {
                    self.counts.record(Suppressed::Unchanged);
                    continue;
                }
            }

            candidates.push(panel);
        }

        if candidates.is_empty() {
            return None;
        }

        for panel in &candidates {
            self.notified.insert(
                panel.id.clone(),
                (panel.status.clone(), *self.epochs.get(&panel.id).unwrap_or(&0)),
            );
        }
        self.counts.emitted += 1;
        self.counts.panels_emitted += candidates.len() as u32;

        Some(coalesce(&candidates))
    }

    /// Record that the session itself lapsed, with no panel payload to blame.
    ///
    /// A 401 carries zero panels, so routing it through [`Self::observe`] with an
    /// empty payload would account for zero observations and leave the
    /// `authenticated_out` counter at 0 -- the counter AC-37-14 asks a reviewer
    /// to read. The lapse is one observation even though it names no panel.
    pub fn note_authenticated_out(&mut self) {
        self.counts.authenticated_out += 1;
    }

    /// Statuses for every panel, for the tray glyph refresh.
    pub fn glyph(&self, payload: &RegistryPayload) -> FleetHealth {
        aggregate_fleet_health(payload)
    }
}

fn status_to_health(status: &str) -> FleetHealth {
    match status {
        "unreachable" => FleetHealth::Unreachable,
        "degraded" => FleetHealth::Degraded,
        "no-health" => FleetHealth::NoHealth,
        "ok" => FleetHealth::Ok,
        // Unrecognised status degrades to unknown rather than guessing.
        _ => FleetHealth::Unknown,
    }
}

/// One toast for many failures, naming up to three ids and the true total.
fn coalesce(panels: &[&Panel]) -> Notification {
    let ids: Vec<String> = panels.iter().take(3).map(|p| p.id.clone()).collect();
    let total = panels.len();

    let title = if total == 1 {
        format!("mem20 - {} needs attention", panels[0].name)
    } else {
        format!("mem20 - {total} subsystems need attention")
    };

    // Copy comes from the backend's own status_reason, verbatim. No cause is
    // asserted that the backend did not state (AC-37-10).
    let body = if total == 1 {
        panels[0]
            .status_reason
            .clone()
            .unwrap_or_else(|| format!("status: {}", panels[0].status))
    } else {
        let names = panels
            .iter()
            .take(3)
            .map(|p| p.id.as_str())
            .collect::<Vec<_>>()
            .join(", ");
        if total > 3 {
            format!("{names} and {} more", total - 3)
        } else {
            names
        }
    };

    Notification {
        title,
        body,
        panel_ids: ids,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn panel(id: &str, status: &str) -> Panel {
        Panel {
            id: id.to_string(),
            name: id.to_string(),
            status: status.to_string(),
            status_reason: Some(format!("{id}: {status}")),
        }
    }

    fn payload(panels: Vec<Panel>, total: u64) -> RegistryPayload {
        RegistryPayload {
            total,
            cached: false,
            age_s: 0.0,
            stale: false,
            sweeping: false,
            panels,
        }
    }

    fn fresh(panels: Vec<Panel>) -> RegistryPayload {
        let total = panels.len() as u64;
        payload(panels, total)
    }

    // ---- aggregation -----------------------------------------------------

    #[test]
    fn all_ok_is_ok_only_when_there_is_something_to_be_ok_about() {
        assert_eq!(
            aggregate_fleet_health(&fresh(vec![panel("a", "ok"), panel("b", "ok")])),
            FleetHealth::Ok
        );
        // Empty fleet is NOT ok by absence of evidence (AC-V1).
        assert_eq!(
            aggregate_fleet_health(&payload(vec![], 0)),
            FleetHealth::Unknown
        );
    }

    #[test]
    fn sweeping_wins_over_everything_and_is_not_an_outage() {
        let mut p = fresh(vec![panel("a", "unreachable")]);
        p.sweeping = true;
        assert_eq!(aggregate_fleet_health(&p), FleetHealth::Starting);
        assert!(!FleetHealth::Starting.is_notification_worthy());
    }

    #[test]
    fn unreachable_outranks_degraded_even_when_degraded_is_more_numerous() {
        // The README warns counts are not orderable; panels are. One
        // unreachable must not be hidden behind three degraded.
        let p = fresh(vec![
            panel("a", "degraded"),
            panel("b", "degraded"),
            panel("c", "degraded"),
            panel("d", "unreachable"),
        ]);
        assert_eq!(aggregate_fleet_health(&p), FleetHealth::Unreachable);
    }

    #[test]
    fn unknown_outranks_no_health_so_a_gap_never_masquerades_as_an_outage() {
        let p = fresh(vec![panel("a", "no-health"), panel("b", "unknown")]);
        assert_eq!(aggregate_fleet_health(&p), FleetHealth::Unknown);
        // ...and no-health alone is still non-ok.
        assert_eq!(
            aggregate_fleet_health(&fresh(vec![panel("a", "no-health")])),
            FleetHealth::NoHealth
        );
    }

    #[test]
    fn ok_mixed_with_an_unrecognised_status_degrades_to_unknown_not_ok() {
        let p = fresh(vec![panel("a", "ok"), panel("b", "something-new")]);
        assert_eq!(aggregate_fleet_health(&p), FleetHealth::Unknown);
    }

    #[test]
    fn only_unreachable_and_degraded_are_notification_worthy() {
        assert!(FleetHealth::Unreachable.is_notification_worthy());
        assert!(FleetHealth::Degraded.is_notification_worthy());
        for quiet in [
            FleetHealth::Ok,
            FleetHealth::NoHealth,
            FleetHealth::Unknown,
            FleetHealth::Starting,
        ] {
            assert!(!quiet.is_notification_worthy(), "{quiet:?} must not notify");
        }
    }

    #[test]
    fn the_tooltip_leads_with_probe_age_and_marks_staleness() {
        let fresh = FleetHealth::Ok.tooltip(3.0, false);
        assert!(fresh.contains("probed 3 s ago"), "{fresh}");
        assert!(!fresh.contains("stale"));

        let stale = FleetHealth::Ok.tooltip(90.0, true);
        assert!(stale.contains("stale"), "{stale}");
        assert!(stale.contains("2 min"), "age must use age_s: {stale}");
    }

    #[test]
    fn a_real_age_is_never_rounded_down_to_zero() {
        // "0 s ago" would make a just-run probe look like it never ran.
        assert_eq!(format_age(0.2), "1 s");
        assert_eq!(format_age(0.0), "1 s");
        assert_eq!(format_age(59.6), "60 s");
        assert_eq!(format_age(60.0), "1 min");
        assert_eq!(format_age(3600.0), "1 h");
    }

    #[test]
    fn a_non_measurement_age_is_not_presented_as_an_age() {
        let tip = FleetHealth::Unknown.tooltip(f64::NAN, false);
        assert_eq!(tip, "Fleet: unknown");
        let neg = FleetHealth::Unknown.tooltip(-5.0, false);
        assert_eq!(neg, "Fleet: unknown");
    }

    #[test]
    fn every_state_has_a_distinct_accessible_name() {
        let names: Vec<&str> = [
            FleetHealth::Starting,
            FleetHealth::Unreachable,
            FleetHealth::Degraded,
            FleetHealth::Unknown,
            FleetHealth::NoHealth,
            FleetHealth::Ok,
        ]
        .iter()
        .map(|s| s.accessible_name())
        .collect();
        let mut unique = names.clone();
        unique.sort_unstable();
        unique.dedup();
        assert_eq!(unique.len(), names.len(), "accessible names must be distinct");
        assert!(names.iter().all(|n| n.starts_with("Fleet: ")));
    }

    #[test]
    fn staleness_is_measured_not_only_trusted() {
        let mut p = payload(vec![panel("a", "ok")], 1);
        assert!(!is_stale(&p));
        p.age_s = STALE_AFTER_S + 1.0;
        // Backend forgot to set the flag; the age still makes it stale.
        assert!(!p.stale);
        assert!(is_stale(&p));
    }

    // ---- notifications ---------------------------------------------------

    #[test]
    fn one_fresh_failure_is_not_enough_two_are() {
        let mut engine = NotificationEngine::new();
        let p = fresh(vec![panel("api", "unreachable")]);

        assert_eq!(engine.observe(&p, true), None, "first sight must stay quiet");
        let n = engine
            .observe(&p, true)
            .expect("second consecutive fresh sweep must notify");
        assert!(n.title.contains("api"));
        assert_eq!(engine.counts.emitted, 1);
    }

    #[test]
    fn cached_sweeps_never_confirm_so_a_frozen_cache_cannot_alarm() {
        let mut engine = NotificationEngine::new();
        let mut p = fresh(vec![panel("api", "unreachable")]);

        engine.observe(&p, true);
        // Ten cached responses must not add confirmation.
        p.cached = true;
        for _ in 0..10 {
            assert_eq!(engine.observe(&p, true), None);
        }
        assert_eq!(engine.counts.emitted, 0);
        assert!(engine.counts.cached >= 10);
    }

    #[test]
    fn two_cached_sweeps_cannot_substitute_for_two_fresh_ones() {
        // The exact failure the doc calls out: cached readings do not count.
        let mut engine = NotificationEngine::new();
        let mut p = fresh(vec![panel("api", "degraded")]);
        p.cached = true;
        assert_eq!(engine.observe(&p, true), None);
        assert_eq!(engine.observe(&p, true), None);
        assert_eq!(engine.counts.emitted, 0);
    }

    #[test]
    fn a_stale_reading_suppresses_everything_for_any_status() {
        let mut engine = NotificationEngine::new();
        let mut p = fresh(vec![panel("api", "unreachable")]);
        p.stale = true;

        for _ in 0..6 {
            assert_eq!(engine.observe(&p, true), None);
        }
        assert_eq!(engine.counts.emitted, 0);
        assert!(engine.counts.stale > 0);
    }

    #[test]
    fn holding_a_panel_down_notifies_exactly_once() {
        let mut engine = NotificationEngine::new();
        let p = fresh(vec![panel("api", "unreachable")]);

        engine.observe(&p, true);
        assert!(engine.observe(&p, true).is_some(), "first transition notifies");

        for _ in 0..6 {
            assert_eq!(engine.observe(&p, true), None, "must not re-notify");
        }
        assert_eq!(engine.counts.emitted, 1);
        assert!(engine.counts.unchanged >= 6);
    }

    #[test]
    fn recovery_then_refailure_is_a_new_transition_and_notifies_again() {
        let mut engine = NotificationEngine::new();
        let down = fresh(vec![panel("api", "unreachable")]);
        let up = fresh(vec![panel("api", "ok")]);

        engine.observe(&down, true);
        assert!(engine.observe(&down, true).is_some());

        // Recovery to `ok` advances the panel's epoch, which re-arms it. Without
        // that, the re-failure below would be deduped against the first toast
        // and never notified -- the T10 case in the doc's matrix.
        engine.observe(&up, true);
        engine.observe(&up, true);

        engine.observe(&down, true);
        assert!(
            engine.observe(&down, true).is_some(),
            "re-failure must notify once more"
        );
        assert_eq!(engine.counts.emitted, 2, "exactly 2, not 3+");
    }

    #[test]
    fn five_panels_failing_together_are_one_notification_naming_three() {
        let mut engine = NotificationEngine::new();
        let p = fresh(vec![
            panel("p1", "unreachable"),
            panel("p2", "unreachable"),
            panel("p3", "unreachable"),
            panel("p4", "unreachable"),
            panel("p5", "unreachable"),
        ]);

        engine.observe(&p, true);
        let n = engine.observe(&p, true).expect("should coalesce");

        assert!(
            n.title.contains('5'),
            "title must state the true total: {}",
            n.title
        );
        assert_eq!(n.panel_ids.len(), 3, "names at most 3");
        assert!(
            n.body.contains("2 more"),
            "body must say how many are unnamed: {}",
            n.body
        );
        assert_eq!(engine.counts.emitted, 1, "one toast, not five");
    }

    #[test]
    fn notification_copy_reuses_the_backend_reason_and_invents_no_cause() {
        let mut engine = NotificationEngine::new();
        let reason = "REST health probe not reachable";
        let p = fresh(vec![Panel {
            id: "api".to_string(),
            name: "API".to_string(),
            status: "unreachable".to_string(),
            status_reason: Some(reason.to_string()),
        }]);

        engine.observe(&p, true);
        let n = engine.observe(&p, true).unwrap();
        assert_eq!(n.body, reason);
        for invented in ["crashed", "OOM", "killed", "restarting"] {
            assert!(
                !n.body.to_lowercase().contains(&invented.to_lowercase()),
                "must not assert a cause the backend did not state"
            );
        }
    }

    #[test]
    fn no_health_and_unknown_never_notify() {
        let mut engine = NotificationEngine::new();
        for status in ["no-health", "unknown"] {
            let p = fresh(vec![panel("x", status)]);
            for _ in 0..5 {
                assert_eq!(engine.observe(&p, true), None, "{status} must not notify");
            }
        }
        assert_eq!(engine.counts.emitted, 0);
    }

    #[test]
    fn signed_out_is_not_an_outage() {
        let mut engine = NotificationEngine::new();
        let p = fresh(vec![panel("api", "unreachable")]);
        for _ in 0..4 {
            assert_eq!(engine.observe(&p, false), None);
        }
        assert_eq!(engine.counts.emitted, 0);
        assert!(engine.counts.authenticated_out > 0);
    }

    #[test]
    fn muting_silences_alerts_without_freezing_the_glyph() {
        let mut engine = NotificationEngine::new();
        engine.set_muted(true);
        let p = fresh(vec![panel("api", "unreachable")]);
        for _ in 0..6 {
            assert_eq!(engine.observe(&p, true), None);
        }
        assert_eq!(engine.counts.emitted, 0);
        assert!(engine.counts.muted > 0);
        // The glyph still tells the truth while muted.
        assert_eq!(engine.glyph(&p), FleetHealth::Unreachable);
    }

    #[test]
    fn every_observation_is_accounted_for_across_a_mixed_sequence() {
        let mut engine = NotificationEngine::new();
        let mut observations = 0u32;

        // A deliberately messy run: fresh, cached, stale and signed out.
        let down = fresh(vec![panel("a", "unreachable"), panel("b", "ok")]);
        let mut cached = down.clone();
        cached.cached = true;
        let mut stale = down.clone();
        stale.stale = true;

        for _ in 0..3 {
            engine.observe(&down, true);
            observations += 2;
        }
        engine.observe(&cached, true);
        observations += 2;
        engine.observe(&stale, true);
        observations += 2;
        engine.observe(&down, false);
        observations += 2;

        assert!(
            engine.counts.is_accounted(observations),
            "counters must cover every observation: {:?} vs {observations}",
            engine.counts
        );
        assert_eq!(engine.counts.panels_emitted, 1, "one panel notified once");
        assert_eq!(engine.counts.emitted, 1);
        // 'a' was pending on its first sweep; 'b' is ok and out of scope.
        assert_eq!(engine.counts.pending_confirmation, 1);
        assert!(
            engine.counts.not_worthy >= 3,
            "ok panels are counted, not dropped"
        );
    }

    #[test]
    fn a_malformed_payload_is_rejected_rather_than_read_as_empty_ok() {
        assert!(RegistryPayload::parse("not json").is_none());
        // Valid JSON with nothing in it parses, and must NOT read as ok.
        let empty = RegistryPayload::parse(r#"{"total":0}"#).unwrap();
        assert_eq!(aggregate_fleet_health(&empty), FleetHealth::Unknown);
    }

    #[test]
    fn one_bad_panel_record_does_not_lose_the_whole_fleet() {
        let p = RegistryPayload::parse(
            r#"{"total":2,"panels":[{"id":"a","name":"A","status":"ok"},{"name":"no-id","status":"ok"}]}"#,
        )
        .unwrap();
        assert_eq!(p.panels.len(), 1, "the panel without an id is skipped");
        assert_eq!(p.total, 2);
    }
}
