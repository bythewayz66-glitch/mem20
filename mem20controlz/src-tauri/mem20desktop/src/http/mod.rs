//! A deliberately small HTTP/1.1 `GET` over `std::net`.
//!
//! Why not `reqwest`? Because the shell asks exactly one question of one
//! loopback port, and because a dependency-free transport is the difference
//! between `cargo test` proving the timeout behaviour in two seconds and it
//! needing a TLS stack to compile. Anything that is not a plain `http://`
//! loopback read is out of scope and says so.
//!
//! The three properties this module is responsible for:
//!
//! * **A timeout always produces an error, never a hang.** Connect and read
//!   budgets are separate, because "the box is up but the app is wedged" and
//!   "nothing is listening" need different remedies.
//! * **A response is bounded.** The reader stops at `max_body`; it does not
//!   read until EOF on a peer that never closes.
//! * **The error text is safe to display.** It names the address and the
//!   failed step. It never contains a response body.

use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};

#[cfg(test)]
mod tests;

/// Default connect budget. Short: loopback either answers immediately or is
/// not there.
pub const DEFAULT_CONNECT_TIMEOUT: Duration = Duration::from_secs(2);

/// Default read budget. The control plane's `/api/health` is a constant-time
/// handler, so a peer that has not finished in this window is wedged.
pub const DEFAULT_READ_TIMEOUT: Duration = Duration::from_secs(5);

/// Default body ceiling. `/api/health` is ~80 bytes; anything approaching this
/// is a misrouted request, not a health check.
pub const DEFAULT_MAX_BODY: usize = 8 * 1024;

#[derive(Debug, Clone, PartialEq)]
pub enum HttpError {
    /// The URL was not a plain `http://host:port/path` we can speak to.
    UnsupportedUrl(String),
    /// Name resolution failed. Only possible for non-literal hosts.
    Resolve(String),
    /// Nothing accepted the connection before the budget elapsed.
    Connect { addr: String, timeout_ms: u64 },
    /// Connected, but the peer did not produce a complete response in budget.
    ReadTimeout { timeout_ms: u64 },
    /// A socket-level failure that is not one of the above.
    Io(String),
    /// The peer spoke something that is not an HTTP/1.x response.
    Malformed(String),
    /// The response headers/body exceeded the configured ceiling.
    TooLarge { limit: usize },
}

impl std::fmt::Display for HttpError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HttpError::UnsupportedUrl(u) => write!(f, "unsupported URL: {u}"),
            HttpError::Resolve(h) => write!(f, "could not resolve host {h}"),
            HttpError::Connect { addr, timeout_ms } => {
                write!(f, "no listener at {addr} after {timeout_ms} ms")
            }
            HttpError::ReadTimeout { timeout_ms } => write!(
                f,
                "peer accepted the connection but did not finish within {timeout_ms} ms"
            ),
            HttpError::Io(msg) => write!(f, "socket error: {msg}"),
            HttpError::Malformed(msg) => write!(f, "malformed HTTP response: {msg}"),
            HttpError::TooLarge { limit } => {
                write!(f, "response exceeded the {limit}-byte ceiling")
            }
        }
    }
}

impl std::error::Error for HttpError {}

/// A minimal HTTP response.
#[derive(Debug, Clone, PartialEq)]
pub struct Response {
    pub status: u16,
    /// Header names are lower-cased for lookup.
    pub headers: Vec<(String, String)>,
    pub body: String,
}

impl Response {
    pub fn header(&self, name: &str) -> Option<&str> {
        let want = name.to_ascii_lowercase();
        self.headers
            .iter()
            .find(|(k, _)| *k == want)
            .map(|(_, v)| v.as_str())
    }

    /// True for 2xx.
    pub fn is_success(&self) -> bool {
        (200..300).contains(&self.status)
    }
}

/// The pieces of a loopback URL this client can serve.
#[derive(Debug, Clone, PartialEq)]
pub struct Target {
    pub host: String,
    pub port: u16,
    pub path: String,
}

/// Parse `http://host:port/path`, rejecting every scheme we cannot speak.
///
/// `https` is rejected by name rather than by falling through to a generic
/// parse error: on a loopback control plane the honest answer is "this build
/// has no TLS", not "bad URL".
pub fn parse_target(url: &str) -> Result<Target, HttpError> {
    if let Some(rest) = url.strip_prefix("https://") {
        return Err(HttpError::UnsupportedUrl(format!(
            "https://{rest} - this build speaks plain http only"
        )));
    }
    let rest = url
        .strip_prefix("http://")
        .ok_or_else(|| HttpError::UnsupportedUrl(url.to_string()))?;

    let (authority, path) = match rest.find('/') {
        Some(idx) => (&rest[..idx], &rest[idx..]),
        None => (rest, "/"),
    };

    if authority.is_empty() {
        return Err(HttpError::UnsupportedUrl(url.to_string()));
    }

    let (host, port) = if let Some(idx) = authority.rfind(':') {
        let (h, p) = (&authority[..idx], &authority[idx + 1..]);
        let port = p
            .parse::<u16>()
            .map_err(|_| HttpError::UnsupportedUrl(format!("bad port in {url}")))?;
        (h.to_string(), port)
    } else {
        (authority.to_string(), 80)
    };

    if host.is_empty() {
        return Err(HttpError::UnsupportedUrl(url.to_string()));
    }

    Ok(Target {
        host,
        port,
        path: path.to_string(),
    })
}

/// Budgets for one request.
#[derive(Debug, Clone, Copy)]
pub struct Limits {
    pub connect_timeout: Duration,
    pub read_timeout: Duration,
    pub max_body: usize,
}

impl Default for Limits {
    fn default() -> Self {
        Self {
            connect_timeout: DEFAULT_CONNECT_TIMEOUT,
            read_timeout: DEFAULT_READ_TIMEOUT,
            max_body: DEFAULT_MAX_BODY,
        }
    }
}

/// `GET url`, returning the response or the precise reason there was none.
pub fn http_get(url: &str, limits: Limits) -> Result<Response, HttpError> {
    let target = parse_target(url)?;
    let addr_text = format!("{}:{}", target.host, target.port);

    let addrs: Vec<_> = (target.host.as_str(), target.port)
        .to_socket_addrs()
        .map_err(|_| HttpError::Resolve(target.host.clone()))?
        .collect();
    if addrs.is_empty() {
        return Err(HttpError::Resolve(target.host.clone()));
    }

    let deadline = Instant::now() + limits.connect_timeout;
    let mut stream: Option<TcpStream> = None;
    for addr in &addrs {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            break;
        }
        if let Ok(s) = TcpStream::connect_timeout(addr, remaining) {
            stream = Some(s);
            break;
        }
    }
    let mut stream = stream.ok_or_else(|| HttpError::Connect {
        addr: addr_text.clone(),
        timeout_ms: limits.connect_timeout.as_millis() as u64,
    })?;

    stream
        .set_read_timeout(Some(limits.read_timeout))
        .map_err(|e| HttpError::Io(e.to_string()))?;
    stream
        .set_write_timeout(Some(limits.read_timeout))
        .map_err(|e| HttpError::Io(e.to_string()))?;

    let request = format!(
        "GET {} HTTP/1.1\r\nHost: {}\r\nAccept: application/json\r\nConnection: close\r\nUser-Agent: mem20controlz-desktop/{}\r\n\r\n",
        target.path,
        addr_text,
        env!("CARGO_PKG_VERSION")
    );
    stream
        .write_all(request.as_bytes())
        .map_err(|e| HttpError::Io(e.to_string()))?;
    stream.flush().map_err(|e| HttpError::Io(e.to_string()))?;

    // Read until the peer closes, or the ceiling is hit.
    let mut raw: Vec<u8> = Vec::with_capacity(1024);
    let mut buf = [0u8; 2048];
    loop {
        match stream.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => {
                raw.extend_from_slice(&buf[..n]);
                if raw.len() > limits.max_body + 8192 {
                    return Err(HttpError::TooLarge {
                        limit: limits.max_body,
                    });
                }
            }
            Err(e)
                if e.kind() == std::io::ErrorKind::WouldBlock
                    || e.kind() == std::io::ErrorKind::TimedOut =>
            {
                return Err(HttpError::ReadTimeout {
                    timeout_ms: limits.read_timeout.as_millis() as u64,
                })
            }
            Err(e) => return Err(HttpError::Io(e.to_string())),
        }
    }

    parse_response(&raw, limits.max_body)
}

/// Split and validate an HTTP/1.x response held in `raw`.
fn parse_response(raw: &[u8], max_body: usize) -> Result<Response, HttpError> {
    let split = raw
        .windows(4)
        .position(|w| w == b"\r\n\r\n")
        .ok_or_else(|| HttpError::Malformed("no header terminator".to_string()))?;

    let head = String::from_utf8_lossy(&raw[..split]).to_string();
    let body_bytes = &raw[split + 4..];

    let mut lines = head.split("\r\n");
    let status_line = lines
        .next()
        .ok_or_else(|| HttpError::Malformed("empty status line".to_string()))?;

    let mut parts = status_line.split_whitespace();
    let version = parts.next().unwrap_or("");
    if !version.starts_with("HTTP/1.") {
        return Err(HttpError::Malformed(format!("status line {status_line:?}")));
    }
    let status = parts
        .next()
        .and_then(|s| s.parse::<u16>().ok())
        .ok_or_else(|| HttpError::Malformed(format!("status line {status_line:?}")))?;

    let mut headers = Vec::new();
    let mut chunked = false;
    let mut content_length: Option<usize> = None;
    for line in lines {
        if line.is_empty() {
            continue;
        }
        let (name, value) = match line.split_once(':') {
            Some((n, v)) => (n.trim().to_ascii_lowercase(), v.trim().to_string()),
            None => continue,
        };
        if name == "transfer-encoding" && value.to_ascii_lowercase().contains("chunked") {
            chunked = true;
        }
        if name == "content-length" {
            content_length = value.parse::<usize>().ok();
        }
        headers.push((name, value));
    }

    if chunked {
        // Out of scope: the control plane sets Content-Length via uvicorn's
        // JSON response path. Refuse rather than mis-decode.
        return Err(HttpError::Malformed(
            "chunked transfer encoding is not supported".to_string(),
        ));
    }

    let body_slice = match content_length {
        Some(n) => {
            if n > max_body {
                return Err(HttpError::TooLarge { limit: max_body });
            }
            &body_bytes[..n.min(body_bytes.len())]
        }
        None => body_bytes,
    };

    if body_slice.len() > max_body {
        return Err(HttpError::TooLarge { limit: max_body });
    }

    Ok(Response {
        status,
        headers,
        body: String::from_utf8_lossy(body_slice).to_string(),
    })
}
