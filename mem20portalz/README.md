# mem20portalz

Customer-facing web portal for authenticated access to a customer's saved mem20 memories.

## What it provides

- **Authenticated, tenant-scoped access:** each account is bound to exactly one mem20 store path. A logged-in customer can access only that store.
- **Memory access API + UI:** browse recent memories, recall by topic/tags, query by semantic/hybrid/graph mode, inspect entities, and view store stats/health diagnostics.
- **Safe-by-default serving:** session auth with HMAC-signed cookies, PBKDF2 password hashing, constant-time comparisons, and sanitized customer responses (internal server filesystem paths are not exposed).

Memory data access is performed through the `mem20api` SDK (`mem20api.open_store` / `MemoryStore` methods), not by importing mem20 engine internals directly.

## Install / run (from repo checkout)

```bash
# from /opt/mem20
PYTHONPATH=/opt/mem20/mem20portalz:/opt/mem20/mem20api \
  python3 -m mem20portalz init-config --config /opt/mem20/secrets/portal_accounts.json

PYTHONPATH=/opt/mem20/mem20portalz:/opt/mem20/mem20api \
  python3 -m mem20portalz add-user \
    --config /opt/mem20/secrets/portal_accounts.json \
    --username alice \
    --store /path/to/alice/store \
    --password 'strong-password'

PYTHONPATH=/opt/mem20/mem20portalz:/opt/mem20/mem20api \
  python3 -m mem20portalz serve \
    --config /opt/mem20/secrets/portal_accounts.json \
    --host 127.0.0.1 --port 8095
```

Open `http://127.0.0.1:8095`.

## Configuration

The portal reads a JSON config file (default: `$MEM20_PORTAL_CONFIG` or `~/.mem20/portal_accounts.json`).

Top-level fields:

- `session_secret` (string, required for login): HMAC secret for signing session cookies.
- `session_ttl_seconds` (int, default `43200`): session lifetime.
- `cookie_secure` (bool, default `false`): set `true` when serving over HTTPS.
- `users` (object): map of username -> account record.

Account record fields:

- `display_name` (string)
- `password_hash` (string, `pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>`)
- `store_path` (string, absolute or `~` path to mem20 store)
- `enabled` (bool, default `true`)
- `created_at` (string, ISO-8601)

## CLI

- `mem20portalz init-config [--config PATH] [--force]`
- `mem20portalz add-user --config PATH --username USER --store PATH --password PASS [--display-name NAME]`
- `mem20portalz set-password --config PATH --username USER --password PASS`
- `mem20portalz enable-user|disable-user --config PATH --username USER`
- `mem20portalz list-users --config PATH`
- `mem20portalz check --config PATH [--username USER]`
- `mem20portalz serve --config PATH [--host 127.0.0.1] [--port 8095]`

## Isolation notes

`mem20api` binds engine store paths via module-global state. To prevent cross-request/cross-tenant races, the portal serializes all store operations through a single process-wide lock and performs blocking store work off the asyncio event loop. This favors correctness/isolation; for higher throughput use per-tenant/per-customer service instances behind an identity-aware gateway.

## API (authenticated unless noted)

- `GET /api/health` (public): service liveness
- `POST /api/auth/login` `{username,password}`: create session
- `POST /api/auth/logout`: clear session
- `GET /api/auth/me`: current account (no store path)
- `GET /api/memories/stats`: sanitized store stats
- `GET /api/memories/health`: sanitized index/ledger health
- `GET /api/memories/ledger?limit=N`: recent ledger events
- `GET /api/memories/browse?limit=N`: recent remembered memories (grounded)
- `POST /api/memories/recall` `{topic?,tags?,k?}`: recall
- `POST /api/memories/query` `{query,mode,k?,topic?,tags?}`: `semantic|hybrid|graph` query
- `GET /api/memories/entities?limit=N`: graph entities

All memory responses are scoped to the authenticated user's configured store.
