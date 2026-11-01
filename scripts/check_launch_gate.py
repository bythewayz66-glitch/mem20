#!/usr/bin/env python3
"""Deterministic launch gate for mem20 public launch channels.

Answers one question: may a Show HN / Product Hunt / Reddit launch begin today?

Gates (all must pass; see docs/gtm/launch-channels-2026-11-01.md section 3):

  1. anonymous        https://mem20.com/ returns 200 to a token-free request
  2. version          served HTML carries the current VERSION and no retired version
  3. social_preview   served HTML carries og:image resolving to an absolute https URL that 200s
  4. https_hop        the canonical Pages URL redirects to https://, not http://
  5. crawlable        robots.txt returns 200
  6. analytics        a privacy-respecting snippet is present, or a waiver is recorded
  7. repo_homepage    the GitHub repo homepage field is not a 403

Exit codes:
  0  every gate passed -> launch may begin
  1  one or more gates failed -> launch is BLOCKED
  2  could not evaluate (network/dependency error) -> treat as BLOCKED

No third-party dependencies. Python 3.9+.

Usage:
    python3 scripts/check_launch_gate.py
    python3 scripts/check_launch_gate.py --json
    python3 scripts/check_launch_gate.py --waive-analytics
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

SITE = "https://mem20.com/"
PAGES = "https://bythewayz66-glitch.github.io/mem20/"
VERSION_URL = "https://raw.githubusercontent.com/bythewayz66-glitch/mem20/main/VERSION"
REPO_API = "https://api.github.com/repos/bythewayz66-glitch/mem20"
ROBOTS = "https://mem20.com/robots.txt"

#: Version strings that must never appear on a launch surface.
RETIRED_VERSIONS = ("v3.0.0", "3.0.0")

#: Privacy-respecting analytics markers. Matched case-insensitively against served HTML.
ANALYTICS_MARKERS = (
    "plausible.io",
    "umami",
    "posthog",
    "gtag(",
    "googletagmanager",
    "fathom",
    "matomo",
    "counter.dev",
    "simpleanalytics",
)

UA = "mem20-launch-gate/1.0 (+https://github.com/bythewayz66-glitch/mem20)"

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_SKIP = "SKIP"


class FetchResult:
    __slots__ = ("url", "status", "body", "headers", "error")

    def __init__(
        self,
        url: str,
        status: Optional[int] = None,
        body: str = "",
        headers: Optional[Dict[str, str]] = None,
        error: Optional[str] = None,
    ) -> None:
        self.url = url
        self.status = status
        self.body = body
        self.headers = headers or {}
        self.error = error

    @property
    def ok(self) -> bool:
        return self.status == 200


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Redirect handler that refuses to follow, so the 301 itself is observable."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401, ANN001
        return None  # returning None makes urllib raise HTTPError for the 3xx


_OPENER_FOLLOW = urllib.request.build_opener()
_OPENER_NOFOLLOW = urllib.request.build_opener(_NoRedirect)


def fetch(url: str, follow: bool = True, timeout: int = 25) -> FetchResult:
    """GET a URL without any access token. Returns status + body, never raises.

    When ``follow`` is False the redirect is returned as its own status code
    instead of being chased, which is how the plaintext-http hop is detected.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    opener = _OPENER_FOLLOW if follow else _OPENER_NOFOLLOW
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read()
            return FetchResult(
                url=url,
                status=resp.status,
                body=raw.decode("utf-8", errors="replace"),
                headers={k.lower(): v for k, v in resp.headers.items()},
            )
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - body is best-effort
            body = ""
        return FetchResult(
            url=url,
            status=exc.code,
            body=body,
            headers={k.lower(): v for k, v in (exc.headers or {}).items()},
        )
    except Exception as exc:  # noqa: BLE001 - network layer, report don't crash
        return FetchResult(url=url, error=f"{type(exc).__name__}: {exc}")


def probe_anonymous(url: str) -> FetchResult:
    """Probe with no redirect following, so a 301 is visible as a 301."""
    return fetch(url, follow=False)


def gate_anonymous(html: FetchResult) -> Dict[str, Any]:
    if html.error:
        return {"gate": "anonymous", "verdict": VERDICT_FAIL, "detail": f"request error: {html.error}"}
    if html.status != 200:
        return {
            "gate": "anonymous",
            "verdict": VERDICT_FAIL,
            "detail": f"{SITE} returned {html.status} to a token-free request (want 200)",
        }
    return {
        "gate": "anonymous",
        "verdict": VERDICT_PASS,
        "detail": f"{SITE} returned 200, {len(html.body.encode('utf-8'))} bytes, no access token",
    }


def get_repo_version() -> Optional[str]:
    res = fetch(VERSION_URL)
    if res.ok and res.body.strip():
        return res.body.strip().splitlines()[0].strip()
    return None


def gate_version(html: FetchResult, repo_version: Optional[str]) -> Dict[str, Any]:
    if html.error or html.status != 200:
        return {
            "gate": "version",
            "verdict": VERDICT_SKIP,
            "detail": "cannot evaluate: site unreachable (see gate 'anonymous')",
        }
    if not repo_version:
        return {
            "gate": "version",
            "verdict": VERDICT_SKIP,
            "detail": f"cannot evaluate: could not read VERSION from {VERSION_URL}",
        }

    served_current = html.body.count(repo_version)
    retired_hits = {v: html.body.count(v) for v in RETIRED_VERSIONS if html.body.count(v)}

    problems: List[str] = []
    if served_current == 0:
        problems.append(f"served page never mentions current version {repo_version}")
    if retired_hits:
        rendered = ", ".join(f"'{v}' x{n}" for v, n in retired_hits.items())
        problems.append(f"served page still carries retired version(s): {rendered}")

    if problems:
        return {
            "gate": "version",
            "verdict": VERDICT_FAIL,
            "detail": "; ".join(problems) + f" (repo VERSION = {repo_version})",
        }
    return {
        "gate": "version",
        "verdict": VERDICT_PASS,
        "detail": f"served page carries {repo_version} x{served_current}; no retired version strings",
    }


OG_IMAGE_RE = re.compile(
    r"""<meta[^>]+(?:property|name)\s*=\s*["']og:image["'][^>]*content\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
TWITTER_CARD_RE = re.compile(
    r"""<meta[^>]+(?:property|name)\s*=\s*["']twitter:card["']""", re.IGNORECASE
)
FAVICON_RE = re.compile(r"""<link[^>]+rel\s*=\s*["'][^"']*icon[^"']*["']""", re.IGNORECASE)


def gate_social_preview(html: FetchResult) -> Dict[str, Any]:
    if html.error or html.status != 200:
        return {
            "gate": "social_preview",
            "verdict": VERDICT_SKIP,
            "detail": "cannot evaluate: site unreachable (see gate 'anonymous')",
        }

    match = OG_IMAGE_RE.search(html.body)
    card = bool(TWITTER_CARD_RE.search(html.body))
    favicon = bool(FAVICON_RE.search(html.body))

    if not match:
        # Product Hunt requires gallery assets; HN/Reddit/Slack render a grey box without this.
        return {
            "gate": "social_preview",
            "verdict": VERDICT_FAIL,
            "detail": (
                "no og:image on the served page -> HN/PH/Reddit/X render a bare grey box "
                f"(twitter:card={'present' if card else 'absent'}, favicon={'present' if favicon else 'absent'})"
            ),
        }

    image_url = match.group(1).strip()
    if not image_url.lower().startswith("https://"):
        return {
            "gate": "social_preview",
            "verdict": VERDICT_FAIL,
            "detail": f"og:image is not an absolute https URL: {image_url}",
        }

    image = fetch(image_url)
    if not image.ok:
        status_detail = image.error if image.error else f"HTTP {image.status}"
        return {
            "gate": "social_preview",
            "verdict": VERDICT_FAIL,
            "detail": f"og:image {image_url} does not resolve anonymously ({status_detail})",
        }

    missing = [name for name, present in (("twitter:card", card), ("favicon", favicon)) if not present]
    detail = f"og:image present and 200: {image_url}"
    if missing:
        detail += f" (still missing: {', '.join(missing)})"
    return {"gate": "social_preview", "verdict": VERDICT_PASS, "detail": detail}


def gate_https_hop() -> Dict[str, Any]:
    res = probe_anonymous(PAGES)
    if res.error:
        return {"gate": "https_hop", "verdict": VERDICT_FAIL, "detail": f"request error: {res.error}"}
    if res.status not in (301, 302, 307, 308):
        return {
            "gate": "https_hop",
            "verdict": VERDICT_FAIL,
            "detail": f"{PAGES} returned {res.status}, expected a 301 redirect to the site",
        }
    location = res.headers.get("location", "")
    if location.lower().startswith("http://"):
        return {
            "gate": "https_hop",
            "verdict": VERDICT_FAIL,
            "detail": f"canonical link hops through plaintext: {res.status} -> {location}",
        }
    if not location.lower().startswith("https://"):
        return {
            "gate": "https_hop",
            "verdict": VERDICT_FAIL,
            "detail": f"redirect target is not an absolute https URL: {location!r}",
        }
    return {
        "gate": "https_hop",
        "verdict": VERDICT_PASS,
        "detail": f"{res.status} -> {location}",
    }


def gate_crawlable() -> Dict[str, Any]:
    res = fetch(ROBOTS)
    if res.error:
        return {"gate": "crawlable", "verdict": VERDICT_FAIL, "detail": f"request error: {res.error}"}
    if not res.ok:
        return {
            "gate": "crawlable",
            "verdict": VERDICT_FAIL,
            "detail": f"robots.txt returned {res.status} (want 200)",
        }
    return {"gate": "crawlable", "verdict": VERDICT_PASS, "detail": "robots.txt returned 200"}


def gate_analytics(html: FetchResult, waived: bool) -> Dict[str, Any]:
    if waived:
        return {
            "gate": "analytics",
            "verdict": VERDICT_PASS,
            "detail": "owner waiver recorded (--waive-analytics): launch runs without on-page attribution",
        }
    if html.error or html.status != 200:
        return {
            "gate": "analytics",
            "verdict": VERDICT_SKIP,
            "detail": "cannot evaluate: site unreachable (see gate 'anonymous')",
        }

    lowered = html.body.lower()
    found = [marker for marker in ANALYTICS_MARKERS if marker in lowered]
    if found:
        return {
            "gate": "analytics",
            "verdict": VERDICT_PASS,
            "detail": f"analytics snippet detected: {', '.join(found)}",
        }
    return {
        "gate": "analytics",
        "verdict": VERDICT_FAIL,
        "detail": (
            "no analytics snippet on the served page -> every utm_* link is decorative and the "
            "Day-7 channel readout is a guess (pass --waive-analytics to accept this in writing)"
        ),
    }


def gate_repo_homepage() -> Dict[str, Any]:
    res = fetch(REPO_API)
    if res.error:
        return {"gate": "repo_homepage", "verdict": VERDICT_FAIL, "detail": f"request error: {res.error}"}
    if not res.ok:
        return {
            "gate": "repo_homepage",
            "verdict": VERDICT_FAIL,
            "detail": f"GitHub API returned {res.status} for {REPO_API}",
        }
    try:
        homepage = (json.loads(res.body) or {}).get("homepage")
    except json.JSONDecodeError as exc:
        return {
            "gate": "repo_homepage",
            "verdict": VERDICT_FAIL,
            "detail": f"could not parse GitHub API response: {exc}",
        }

    if not homepage:
        return {
            "gate": "repo_homepage",
            "verdict": VERDICT_FAIL,
            "detail": "repo homepage field is empty -> the most-clicked link on the repo goes nowhere",
        }

    probe = fetch(homepage)
    if probe.error:
        return {
            "gate": "repo_homepage",
            "verdict": VERDICT_FAIL,
            "detail": f"repo homepage {homepage} is unreachable ({probe.error})",
        }
    if not probe.ok:
        hint = ""
        if "/sites/" in homepage:
            hint = " - this is a /sites/ artifact, which is project-member-only and always 403s"
        return {
            "gate": "repo_homepage",
            "verdict": VERDICT_FAIL,
            "detail": f"repo homepage {homepage} returned {probe.status}{hint}",
        }
    return {
        "gate": "repo_homepage",
        "verdict": VERDICT_PASS,
        "detail": f"repo homepage {homepage} returned 200",
    }


def evaluate(waived: bool = False) -> Dict[str, Any]:
    html = fetch(SITE)
    repo_version = get_repo_version()

    gates = [
        gate_anonymous(html),
        gate_version(html, repo_version),
        gate_social_preview(html),
        gate_https_hop(),
        gate_crawlable(),
        gate_analytics(html, waived),
        gate_repo_homepage(),
    ]

    failed = [g for g in gates if g["verdict"] == VERDICT_FAIL]
    passed = [g for g in gates if g["verdict"] == VERDICT_PASS]

    return {
        "gates": gates,
        "passed": len(passed),
        "failed": len(failed),
        "total": len(gates),
        "launchable": not failed,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether mem20 may begin a public launch (Show HN / Product Hunt / Reddit).",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--waive-analytics",
        action="store_true",
        help="treat the missing analytics snippet as an accepted owner decision instead of a failure",
    )
    args = parser.parse_args(argv)

    try:
        report = evaluate(waived=args.waive_analytics)
    except Exception as exc:  # noqa: BLE001 - a gate that cannot run is a blocked gate
        if args.json:
            print(json.dumps({"launchable": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        else:
            print(f"LAUNCH GATE: COULD NOT EVALUATE ({type(exc).__name__}: {exc})")
            print("Treating as BLOCKED.")
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["launchable"] else 1

    print("mem20 launch gate")
    print(f"  site   : {SITE}")
    print(f"  pages  : {PAGES}")
    print()
    for gate in report["gates"]:
        print(f"  [{gate['verdict']:4}] {gate['gate']:<15} {gate['detail']}")
    print()

    if report["launchable"]:
        print(f"LAUNCH GATE: OPEN - {report['passed']}/{report['total']} gates passed.")
        print("Show HN may go out. Follow the sequencing in docs/gtm/launch-channels-2026-11-01.md section 4.")
        return 0

    print(
        f"LAUNCH GATE: BLOCKED - {report['failed']} of {report['total']} gates failed, "
        f"{report['passed']} passed."
    )
    print("Do not post to Show HN, Product Hunt or Reddit until every gate passes.")
    print("See docs/gtm/launch-channels-2026-11-01.md section 3.1 for the minimum unblock.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
