//! Socket-level tests for [`super`].
//!
//! These run real one-shot listeners on an ephemeral port rather than mocking
//! the transport, so what is exercised is the kernel's actual timeout and
//! close behaviour -- which is the whole point of the module.

use super::*;
use std::net::TcpListener;
use std::thread;

fn limits() -> Limits {
    Limits {
        connect_timeout: Duration::from_millis(300),
        read_timeout: Duration::from_millis(700),
        max_body: 4096,
    }
}

/// Bind a one-shot server on an OS-chosen port, run `handler` on a thread,
/// return its URL and a join handle. Port 0 keeps parallel tests apart.
fn serve(handler: impl FnOnce(TcpStream) + Send + 'static) -> (String, thread::JoinHandle<()>) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind ephemeral port");
    let port = listener.local_addr().unwrap().port();
    let handle = thread::spawn(move || {
        if let Ok((stream, _)) = listener.accept() {
            handler(stream);
        }
    });
    (format!("http://127.0.0.1:{port}/api/health"), handle)
}

#[test]
fn parses_a_loopback_target_with_path() {
    let t = parse_target("http://127.0.0.1:8890/api/health").unwrap();
    assert_eq!(t.host, "127.0.0.1");
    assert_eq!(t.port, 8890);
    assert_eq!(t.path, "/api/health");
}

#[test]
fn defaults_the_path_to_root_and_the_port_to_80() {
    let t = parse_target("http://localhost").unwrap();
    assert_eq!(t.port, 80);
    assert_eq!(t.path, "/");
}

#[test]
fn https_is_refused_by_name_so_the_reason_is_readable() {
    let err = parse_target("https://127.0.0.1:8890/api/health").unwrap_err();
    match err {
        HttpError::UnsupportedUrl(msg) => assert!(msg.contains("plain http only")),
        other => panic!("expected UnsupportedUrl, got {other:?}"),
    }
}

#[test]
fn a_non_http_scheme_is_refused() {
    // Only the scheme matters here; any non-http scheme must be turned away
    // rather than handed to the TCP layer.
    assert!(matches!(
        parse_target("file://remote-host/some/path"),
        Err(HttpError::UnsupportedUrl(_))
    ));
}

#[test]
fn reads_a_complete_json_response() {
    let (url, handle) = serve(|mut s| {
        let mut buf = [0u8; 1024];
        let _ = s.read(&mut buf);
        let body =
            r#"{"status":"ok","service":"mem20-control","version":"0.1.0","uptime_s":1.5}"#;
        let resp = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
            body.len(),
            body
        );
        let _ = s.write_all(resp.as_bytes());
    });

    let resp = http_get(&url, limits()).expect("request should succeed");
    assert_eq!(resp.status, 200);
    assert!(resp.is_success());
    assert_eq!(resp.header("content-type"), Some("application/json"));
    assert!(resp.body.contains("mem20-control"));
    handle.join().unwrap();
}

#[test]
fn a_slow_peer_produces_a_read_timeout_not_a_hang() {
    // Accept, then never answer. The client must give up on its own budget.
    let (url, handle) = serve(|_s| {
        thread::sleep(Duration::from_millis(1500));
    });

    let started = Instant::now();
    let err = http_get(&url, limits()).unwrap_err();
    let elapsed = started.elapsed();

    assert!(
        matches!(err, HttpError::ReadTimeout { .. }),
        "expected ReadTimeout, got {err:?}"
    );
    assert!(
        elapsed < Duration::from_millis(1400),
        "client waited {elapsed:?}, past its own budget"
    );
    handle.join().unwrap();
}

#[test]
fn nothing_listening_produces_a_connect_error_naming_the_address() {
    // Bind then drop, so the port is free and nothing is listening on it.
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    drop(listener);

    let url = format!("http://127.0.0.1:{port}/api/health");
    match http_get(&url, limits()) {
        Err(HttpError::Connect { addr, .. }) => assert!(addr.contains(&port.to_string())),
        other => panic!("expected Connect, got {other:?}"),
    }
}

#[test]
fn a_garbage_response_is_rejected_rather_than_guessed_at() {
    let (url, handle) = serve(|mut s| {
        let mut buf = [0u8; 1024];
        let _ = s.read(&mut buf);
        let _ = s.write_all(b"SSH-2.0-OpenSSH_9.6\r\n\r\n");
    });
    assert!(matches!(
        http_get(&url, limits()),
        Err(HttpError::Malformed(_))
    ));
    handle.join().unwrap();
}

#[test]
fn an_oversized_content_length_is_refused_before_reading_it() {
    let (url, handle) = serve(|mut s| {
        let mut buf = [0u8; 1024];
        let _ = s.read(&mut buf);
        let resp = "HTTP/1.1 200 OK\r\nContent-Length: 999999\r\n\r\n";
        let _ = s.write_all(resp.as_bytes());
    });
    assert!(matches!(
        http_get(&url, limits()),
        Err(HttpError::TooLarge { .. })
    ));
    handle.join().unwrap();
}

#[test]
fn a_non_2xx_status_is_returned_not_turned_into_an_io_error() {
    let (url, handle) = serve(|mut s| {
        let mut buf = [0u8; 1024];
        let _ = s.read(&mut buf);
        let body = r#"{"detail":"unauthorized"}"#;
        let resp = format!(
            "HTTP/1.1 401 Unauthorized\r\nContent-Length: {}\r\n\r\n{}",
            body.len(),
            body
        );
        let _ = s.write_all(resp.as_bytes());
    });
    let resp = http_get(&url, limits()).expect("401 is a response, not a transport error");
    assert_eq!(resp.status, 401);
    assert!(!resp.is_success());
    handle.join().unwrap();
}

#[test]
fn request_line_and_host_header_carry_the_target_path() {
    let (url, handle) = serve(|mut s| {
        let mut buf = [0u8; 2048];
        let n = s.read(&mut buf).unwrap_or(0);
        let text = String::from_utf8_lossy(&buf[..n]).to_string();
        assert!(
            text.starts_with("GET /api/health HTTP/1.1\r\n"),
            "got {text:?}"
        );
        assert!(text.contains("Host: 127.0.0.1:"), "got {text:?}");
        let _ = s.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}");
    });
    let _ = http_get(&url, limits());
    handle.join().unwrap();
}
