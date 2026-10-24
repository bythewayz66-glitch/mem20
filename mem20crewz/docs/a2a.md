# A2A peer contract (mem20crewz)

## Peer file (`peers.yaml`)

Top-level key `a2a_agents`. Each entry:

```yaml
a2a_agents:
  <peer-name>:
    url: http://localhost:<port>
    timeout: <seconds>
    capabilities: [tag, ...]
```

- `url`: JSON-RPC v1.0 endpoint of the peer (loopback by default).
- `timeout`: per-call timeout in seconds.
- `capabilities`: tags used for peer selection/routing.

Port range: 9901–9922 (22 peers).

## JSON-RPC frame

Requests are JSON-RPC v1.0 over HTTP POST to `<url>`. A call carries
`method`, `params`, and `id`. Responses carry `result` or `error`.

## Timeouts and failure semantics

- Per-peer `timeout` caps a single call; on expiry the peer is marked failed
  and the call returns an error result.
- `fan_out` runs peers in parallel; partial failures are reported per peer
  rather than aborting the whole fan-out.
- Missing/unreachable peers are skipped with a recorded error.

## Client API

`A2AClient` (in `a2a.py`) exposes `peer_names()`, `peers()`,
`discover()`, `call(peer, method, params)`, and `fan_out(peers, method, params)`.
