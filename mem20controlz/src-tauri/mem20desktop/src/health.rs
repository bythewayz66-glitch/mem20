//! Parsing and scoring of `GET /api/health`.
//!
//! `mem20controlz/mem20controlz/app.py::health` returns exactly:
//!
//! ```json
//! { "status": "ok", "service": "mem20-control", "version": "0.1.0", "uptime_s": 12.5 }
//! ```
//!
//! Two properties of that route drive everything below.
//!
//! 1. **`status` is a hard-coded literal `"ok"`.** It asserts that this process
//!    answered — never that the fleet behind it is healthy. So nothing in this
//!    module may translate an `"ok"` health body into a claim about fleet
//!    health. Fleet health comes from `/api/registry` and belongs to #37.
//! 2. **The route is unauthenticated.** That makes it the only thing the shell
//!    may call before a session exists, and it is also why a response is not
//!    proof of identity: anything could be listening on the port.
//!
//! Hence [`assess`] treats "service is absent" as *not ours* rather than as
//! ours-by-default. Guessing wrong in the other direction produces a shell
//! that cheerfully reports a healthy control plane while talking to a
//! stale dev server on the same port.

use serde_json::Value;

/// The `service` string `app.py::health` reports. A response that does not
/// carry it is not this control plane.
pub const CONTROL_PLANE_SERVICE: &str = "mem20-control";

/// A `/api/health` body, parsed as leniently as the contract allows.
#[derive(Debug, Clone, PartialEq)]
pub struct HealthBody {
    /// Reported status. Required: a health body without a status is not a
    /// health body.
    pub status: String,
    /// Self-reported service identity. `None` when the peer omitted it — which
    /// [`assess`] does *not* treat as ours.
    pub service: Option<String>,
    pub version: Option<String>,
    /// Uptime in seconds, only when the peer sent a finite, non-negative
    /// number. `None` means "absent, or not trustworthy enough to display".
    pub uptime_s: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HealthError {
    /// The body was not valid JSON, or not a JSON object.
    NotAnObject,
    /// `status` was missing, or present but not a string.
    MissingStatus,
    /// The body exceeded the size ceiling before parsing.
    TooLarge { bytes: usize, limit: usize },
}

impl std::fmt::Display for HealthError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HealthError::NotAnObject => write!(f, "health response was not a JSON object"),
            HealthError::MissingStatus => {
                write!(f, "health response had no string `status` field")
            }
            HealthError::TooLarge { bytes, limit } => write!(
                f,
                "health response was {bytes} bytes, over the {limit}-byte ceiling"
            ),
        }
    }
}

impl std::error::Error for HealthError {}

/// A health body larger than this is not a health body — it is a misrouted
/// request (an HTML error page, a bundle) that we refuse to parse.
pub const MAX_HEALTH_BODY_BYTES: usize = 8 * 1024;

/// Parse a `/api/health` body.
///
/// Shape only: this function never decides whether the peer is healthy. Pair
/// it with [`assess`].
pub fn parse_health_body(raw: &str) -> Result<HealthBody, HealthError> {
    if raw.len() > MAX_HEALTH_BODY_BYTES {
        return Err(HealthError::TooLarge {
            bytes: raw.len(),
            limit: MAX_HEALTH_BODY_BYTES,
        });
    }

    let value: Value = serde_json::from_str(raw).map_err(|_| HealthError::NotAnObject)?;
    let object = value.as_object().ok_or(HealthError::NotAnObject)?;

    let status = object
        .get("status")
        .and_then(Value::as_str)
        .ok_or(HealthError::MissingStatus)?
        .to_string();

    let service = object
        .get("service")
        .and_then(Value::as_str)
        .map(str::to_string);

    let version = object
        .get("version")
        .and_then(Value::as_str)
        .map(str::to_string);

    // A negative or non-finite uptime is a bug in the peer. Dropping it to
    // `None` keeps the shell from rendering "-3 s uptime" as fact.
    let uptime_s = object
        .get("uptime_s")
        .and_then(Value::as_f64)
        .filter(|s| s.is_finite() && *s >= 0.0);

    Ok(HealthBody {
        status,
        service,
        version,
        uptime_s,
    })
}

/// What the shell is allowed to claim about the control plane.
///
/// Deliberately *not* the five-value panel vocabulary from `README.md` §1.1:
/// that vocabulary describes fleet panels, and reusing its words for a single
/// process would invite the reader to confuse liveness with health.
#[derive(Debug, Clone, PartialEq)]
pub enum ControlPlaneLiveness {
    /// No probe has completed since the shell started.
    Unknown,
    /// A probe is in flight. Transient; cleared by the next result.
    Starting,
    /// Ours, and it answered `status: "ok"`. Version/uptime are for display.
    Up {
        version: Option<String>,
        uptime_s: Option<f64>,
    },
    /// Ours, but it answered with a status other than `"ok"`.
    NotOk { reported: String },
    /// Something answered, but it did not identify as this control plane.
    /// `service` is whatever it did call itself, when it said anything.
    Foreign { service: Option<String> },
    /// Nothing answered: connection refused, timeout, TLS-less transport error.
    Unreachable { reason: String },
}

impl ControlPlaneLiveness {
    /// True when the shell has a positive, evidenced reason to show "up".
    pub fn is_up(&self) -> bool {
        matches!(self, ControlPlaneLiveness::Up { .. })
    }

    /// True when the shell should offer a remedy (retry, start the service)
    /// rather than quietly doing nothing.
    pub fn needs_attention(&self) -> bool {
        matches!(
            self,
            ControlPlaneLiveness::NotOk { .. }
                | ControlPlaneLiveness::Foreign { .. }
                | ControlPlaneLiveness::Unreachable { .. }
        )
    }

    /// One-line text for the shell status strip. Never asserts a cause the
    /// peer did not state.
    pub fn summary(&self) -> String {
        match self {
            ControlPlaneLiveness::Unknown => "control plane: not probed yet".to_string(),
            ControlPlaneLiveness::Starting => "control plane: probing...".to_string(),
            ControlPlaneLiveness::Up {
                version,
                uptime_s,
            } => {
                let ver = version.as_deref().unwrap_or("version not reported");
                match uptime_s {
                    Some(s) => format!("control plane up - {ver} - uptime {}", format_age(*s)),
                    None => format!("control plane up - {ver}"),
                }
            }
            ControlPlaneLiveness::NotOk { reported } => {
                format!("control plane answered with status {reported:?}")
            }
            ControlPlaneLiveness::Foreign { service: Some(name) } => format!(
                "port is answering, but as {name:?} - not the mem20 control plane"
            ),
            ControlPlaneLiveness::Foreign { service: None } => {
                "port is answering, but the responder did not identify as the mem20 control plane"
                    .to_string()
            }
            ControlPlaneLiveness::Unreachable { reason } => {
                format!("control plane unreachable: {reason}")
            }
        }
    }
}

/// Score a parsed health body against the identity + status contract.
///
/// Order matters and the first match wins:
///
/// 1. wrong/absent `service` -> [`ControlPlaneLiveness::Foreign`]. Identity is
///    checked *before* status so a foreign `"ok"` can never read as ours.
/// 2. `status == "ok"` -> [`ControlPlaneLiveness::Up`].
/// 3. anything else -> [`ControlPlaneLiveness::NotOk`].
pub fn assess(body: &HealthBody) -> ControlPlaneLiveness {
    match body.service.as_deref() {
        Some(CONTROL_PLANE_SERVICE) => {}
        other => {
            return ControlPlaneLiveness::Foreign {
                service: other.map(str::to_string),
            }
        }
    }

    if body.status == "ok" {
        ControlPlaneLiveness::Up {
            version: body.version.clone(),
            uptime_s: body.uptime_s,
        }
    } else {
        ControlPlaneLiveness::NotOk {
            reported: body.status.clone(),
        }
    }
}

/// An assessment plus how old the evidence is.
///
/// The age travels with the verdict on purpose. A UI that shows "up" from a
/// probe sixty seconds old, with no hint that it is sixty seconds old, is
/// showing a cached reading as a live one. Carrying the age in the type means
/// the renderer cannot accidentally drop it.
#[derive(Debug, Clone, PartialEq)]
pub struct Assessment {
    pub liveness: ControlPlaneLiveness,
    /// Seconds since the probe that produced `liveness` completed.
    pub age_s: f64,
}

impl Assessment {
    pub fn new(liveness: ControlPlaneLiveness, age_s: f64) -> Self {
        Self {
            liveness,
            age_s: if age_s.is_finite() && age_s >= 0.0 {
                age_s
            } else {
                0.0
            },
        }
    }

    /// A reading older than this is presented as stale rather than current.
    pub const STALE_AFTER_S: f64 = 45.0;

    pub fn is_stale(&self) -> bool {
        self.age_s > Self::STALE_AFTER_S
    }

    /// Status-strip text, always carrying the probe age once there is one.
    pub fn summary(&self) -> String {
        let base = self.liveness.summary();
        match self.liveness {
            ControlPlaneLiveness::Unknown | ControlPlaneLiveness::Starting => base,
            _ if self.is_stale() => {
                format!("{base} - last probed {} ago", format_age(self.age_s))
            }
            _ => base,
        }
    }
}

/// Human-readable duration, using the largest unit that keeps the number >= 1.
///
/// `format_age(3600.0)` is `"1 h"`, never `"60 min"`. That exact confusion
/// shipped once in this project's frontend (`formatAge(3600)` rendering as
/// `60 min`) and is pinned by a test below so it cannot come back.
pub fn format_age(seconds: f64) -> String {
    if !seconds.is_finite() || seconds < 0.0 {
        return "unknown".to_string();
    }
    let s = seconds as u64;
    if s < 60 {
        return format!("{s} s");
    }
    let minutes = s / 60;
    if minutes < 60 {
        return format!("{minutes} min");
    }
    let hours = minutes / 60;
    if hours < 24 {
        return format!("{hours} h");
    }
    format!("{} d", hours / 24)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn body(json: &str) -> HealthBody {
        parse_health_body(json).expect("fixture should parse")
    }

    #[test]
    fn parses_the_exact_payload_app_py_returns() {
        let b = body(
            r#"{"status":"ok","service":"mem20-control","version":"0.1.0","uptime_s":12.5}"#,
        );
        assert_eq!(b.status, "ok");
        assert_eq!(b.service.as_deref(), Some(CONTROL_PLANE_SERVICE));
        assert_eq!(b.version.as_deref(), Some("0.1.0"));
        assert_eq!(b.uptime_s, Some(12.5));
    }

    #[test]
    fn rejects_non_json_and_non_object_bodies() {
        assert_eq!(parse_health_body("not json"), Err(HealthError::NotAnObject));
        assert_eq!(parse_health_body("[1,2,3]"), Err(HealthError::NotAnObject));
        assert_eq!(parse_health_body("\"ok\""), Err(HealthError::NotAnObject));
    }

    #[test]
    fn rejects_a_body_without_a_string_status() {
        assert_eq!(
            parse_health_body(r#"{"service":"mem20-control"}"#),
            Err(HealthError::MissingStatus)
        );
        assert_eq!(
            parse_health_body(r#"{"status":200,"service":"mem20-control"}"#),
            Err(HealthError::MissingStatus)
        );
    }

    #[test]
    fn rejects_an_oversized_body_instead_of_parsing_it() {
        let huge = format!(
            r#"{{"status":"ok","pad":"{}"}}"#,
            "x".repeat(MAX_HEALTH_BODY_BYTES)
        );
        assert!(matches!(
            parse_health_body(&huge),
            Err(HealthError::TooLarge { .. })
        ));
    }

    #[test]
    fn uptime_is_dropped_when_it_is_negative_or_not_a_number() {
        assert_eq!(
            body(r#"{"status":"ok","service":"mem20-control","uptime_s":-3}"#).uptime_s,
            None
        );
        assert_eq!(
            body(r#"{"status":"ok","service":"mem20-control","uptime_s":"12"}"#).uptime_s,
            None
        );
    }

    #[test]
    fn our_service_reporting_ok_is_up() {
        let verdict = assess(&body(
            r#"{"status":"ok","service":"mem20-control","version":"0.1.0","uptime_s":5}"#,
        ));
        assert!(verdict.is_up());
        assert!(!verdict.needs_attention());
        assert!(matches!(
            verdict,
            ControlPlaneLiveness::Up {
                uptime_s: Some(_),
                ..
            }
        ));
    }

    #[test]
    fn an_absent_service_field_is_never_treated_as_ours() {
        // The failure this prevents: a dev server or a proxy answers "ok" and
        // the shell tells the user the control plane is running.
        let verdict = assess(&body(r#"{"status":"ok"}"#));
        assert_eq!(verdict, ControlPlaneLiveness::Foreign { service: None });
        assert!(!verdict.is_up());
        assert!(verdict.needs_attention());
    }

    #[test]
    fn a_different_service_reporting_ok_is_foreign_not_up() {
        let verdict = assess(&body(r#"{"status":"ok","service":"some-other-thing"}"#));
        assert_eq!(
            verdict,
            ControlPlaneLiveness::Foreign {
                service: Some("some-other-thing".to_string())
            }
        );
        assert!(!verdict.is_up());
    }

    #[test]
    fn identity_is_checked_before_status() {
        // Same body, only the service differs: the verdict must differ even
        // though both say "ok". If status were checked first both would be Up.
        let ours = assess(&body(r#"{"status":"ok","service":"mem20-control"}"#));
        let theirs = assess(&body(r#"{"status":"ok","service":"mem20-web"}"#));
        assert!(ours.is_up());
        assert!(!theirs.is_up());
    }

    #[test]
    fn our_service_reporting_a_non_ok_status_is_not_ok_not_unreachable() {
        let verdict = assess(&body(r#"{"status":"degraded","service":"mem20-control"}"#));
        assert_eq!(
            verdict,
            ControlPlaneLiveness::NotOk {
                reported: "degraded".to_string()
            }
        );
        // It answered; calling it unreachable would send the user to restart
        // a process that is already running.
        assert!(!matches!(verdict, ControlPlaneLiveness::Unreachable { .. }));
    }

    #[test]
    fn unreachable_is_reserved_for_transport_failure() {
        let verdict = ControlPlaneLiveness::Unreachable {
            reason: "connection refused".to_string(),
        };
        assert!(verdict.needs_attention());
        assert!(!verdict.is_up());
        assert!(verdict.summary().contains("connection refused"));
    }

    #[test]
    fn format_age_uses_the_largest_unit_that_keeps_the_number_at_least_one() {
        assert_eq!(format_age(0.0), "0 s");
        assert_eq!(format_age(59.0), "59 s");
        assert_eq!(format_age(60.0), "1 min");
        assert_eq!(format_age(3599.0), "59 min");
        // The regression that shipped before: 3600 must not read "60 min".
        assert_eq!(format_age(3600.0), "1 h");
        assert_eq!(format_age(7200.0), "2 h");
        assert_eq!(format_age(86_400.0), "1 d");
    }

    #[test]
    fn format_age_refuses_to_invent_a_duration() {
        assert_eq!(format_age(-1.0), "unknown");
        assert_eq!(format_age(f64::NAN), "unknown");
        assert_eq!(format_age(f64::INFINITY), "unknown");
    }

    #[test]
    fn an_unknown_verdict_is_not_up_and_is_not_a_reason_to_alarm() {
        let a = Assessment::new(ControlPlaneLiveness::Unknown, 0.0);
        assert!(!a.liveness.is_up());
        // Nothing has been probed yet: annoying the user would be premature.
        assert!(!a.liveness.needs_attention());
        assert_eq!(a.summary(), "control plane: not probed yet");
    }

    #[test]
    fn age_is_carried_and_staleness_is_reported_in_the_summary() {
        let fresh = Assessment::new(
            ControlPlaneLiveness::Up {
                version: Some("0.1.0".to_string()),
                uptime_s: Some(5.0),
            },
            10.0,
        );
        assert!(!fresh.is_stale());
        assert!(!fresh.summary().contains("last probed"));

        let stale = Assessment::new(fresh.liveness.clone(), 90.0);
        assert!(stale.is_stale());
        assert!(stale.summary().contains("last probed 1 min ago"));
    }

    #[test]
    fn a_negative_age_cannot_manufacture_a_fresh_reading() {
        let a = Assessment::new(ControlPlaneLiveness::Unknown, -30.0);
        assert_eq!(a.age_s, 0.0);
        assert!(!a.is_stale());
    }
}
