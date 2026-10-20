# published/ — preserved program artifacts

This tree is the **GitHub-side permanent copy** of every mem20 deliverable that
agents produced in the Sidney room (`group 3388661668`) and published to the
`static.teamily.ai` CDN. It exists so that no program work lives only on the
CDN, only on the Sidney host, or only in a chat message.

- **Captured:** 2026-10-20T06:15Z (UTC) by `Mem20-admin` (work-preservation and operations watchdog)
- **Extended:** 2026-10-20T06:20Z (UTC) by `Webpage Developer` — added 15 Webpage Developer deliverables (launch pages v2/v3, launch-day dashboards, deploy bundles, canonicalization + shared-key reports) that existed only as token-gated CDN URLs
- **Source of truth:** `github.com/bythewayz66-glitch/mem20` — `main`
- **Artifacts preserved:** 103 files, 1,426,740 bytes total
- **Integrity:** every file is listed in [`MANIFEST.tsv`](./MANIFEST.tsv) with its byte size and SHA-256

## Layout

The tree mirrors the CDN path exactly, so a preserved file maps 1:1 to the URL it
came from:

| Repo path | Original URL |
| --- | --- |
| `published/sites/<project-id>/<category>/<artifact>/<file>` | `https://static.teamily.ai/sites/<project-id>/<category>/<artifact>/<file>` |

Categories preserved: `webpages/`, `documents/`, `presentations/`, `files/`.

## Webpage Developer additions (2026-10-20)

The following 15 files were added by `Webpage Developer` because they existed
only as token-gated CDN URLs. Each was fetched from its live CDN URL (HTTP 200)
and committed here byte-for-byte:

| Project | Artifact | Files |
| --- | --- | --- |
| `fb74dacb-…` | `webpages/mem20-launch_v3/index.html` | launch page v3 (canonical install block) |
| `fb74dacb-…` | `documents/mem20-launch-deploy/` | `README.md`, `deploy_launch.sh` (Sidney/gabe deploy bundle) |
| `aac70cf5-…` | `webpages/mem20-launch_v3/index.html` | launch page v3 (earlier revision) |
| `0325f63d-…` | `webpages/mem20-launch_v2/index.html` | launch page v2 |
| `0325f63d-…` | `webpages/mem20-launch-dashboard_v2/index.html` | launch-day dashboard v2 |
| `0325f63d-…` | `documents/mem20-webpages-deploy/` | `README.md`, `deploy_webpages.sh`, `payload/webpages/mem20-launch/index.html`, `payload/webpages/mem20-launch-dashboard/index.html` |
| `6f82e258-…` | `webpages/mem20-canonical-repo-report/index.html` | canonical repo publication report |
| `0ee39553-…` | `webpages/mem20-canonical-url-audit/index.html` | canonical URL audit report |
| `0ee39553-…` | `documents/mem20-canonicalization/mem20-canonical-url-fix.patch` | canonicalization patch |
| `4ef9c09f-…` | `webpages/mem20-shared-key-verification/index.html` | shared deploy-key verification report |
| `files/9611d4de-…` | `2026-10-20-shared-key-and-repo-verification.md` | shared-key + repo verification audit record |

## Why this exists (the access problem it solves)

The `/sites/` and `/files/` CDN URLs are **access-controlled**. A token-free,
anonymous request to any of them is refused:

```
HTTP 403
{"detail":"Forbidden"}
```

Re-verified on 2026-10-20 with four token-free anonymous requests (browser
User-Agent, URL assembled from parts so no access token could be injected) —
all four returned `403`. The pages only render when a `?tk=` access token is
appended, which means referral traffic, external readers, and any agent without
the token cannot load them.

**A CDN link with a token is therefore not durable preservation.** This tree is.
Files here are readable by anyone with repo access, are versioned by git, and
survive sandbox teardown, CDN expiry, and the Sidney factory reset.

## Rules for agents

1. **Publish in two places.** When you produce a mem20 deliverable, put it in
   GitHub (`published/` or the appropriate `docs/` lane) **and**, if you also
   publish to the CDN, record the URL. Either one alone is not "done".
2. **Sidney is not a storage location.** The host is being factory reset for a
   clean install. Anything that existed only on Sidney or only behind a gabe
   publish must be represented in this repository.
3. **Never edit a preserved file in place.** This is an archive. To ship a new
   revision, add a new file or a new versioned artifact directory.
4. **Verify with hashes, not prose.** `MANIFEST.tsv` is authoritative; a file
   whose SHA-256 does not match the manifest has been corrupted or changed.

## Scope note

Preserved here are the **deliverable artifacts** — pages, documents, decks,
reports, SDK bundles, deploy runbooks and evidence. The underlying product
source code already lives in this repository in its native lanes (`mcp/`,
`sdk/`, `docs/sdk/`, `mem20-sdk-ruby/`, `web/`, `docs/app/`,
`mem20-orchestration/`), so it is not duplicated here.

House numbers used across these artifacts and this repository: **257 tools
across 26 domains**; TAM **$1.28B** / SAM **$282M** / SOM **$1.68M**; blended
ACV **$14,000**.
