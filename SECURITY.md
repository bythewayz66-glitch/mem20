# Security policy

## Reporting a vulnerability

**Do not open a public issue.** Use GitHub's private reporting channel:

https://github.com/bythewayz66-glitch/mem20/security/advisories/new

Please include: affected component, a minimal reproduction, the impact, and any
suggested fix. You will get an acknowledgement, then a resolution timeline.

## Scope

mem20 runs an MCP tool server and reaches the local filesystem, a memory store,
and external APIs. The following are in scope:

- Path traversal or sandbox escape through the filesystem tools.
- Command injection through the blender / unity / shell bridges.
- Secret or token leakage (`.env`, `secrets/`, ledger entries, logs).
- Approval-gate bypass: a tool that mutates state without passing the approval
  path.
- Namespace / ACL circumvention in the memory store.

## Handling of secrets

Secrets belong in `secrets/` or the environment, never in the tree.
`secrets/`, `.env`, `*.key`, `*.pem` are git-ignored - keep it that way. If you
find a committed secret, report it privately and rotate the credential; do not
paste the value into the issue.

## Supported versions

The latest `main` and the most recent tagged release are supported.
