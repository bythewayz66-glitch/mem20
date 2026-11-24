# mem20 Port Map

Verified from live listeners (`ss -ltnp`) and every unit's `ExecStart` on 2026-11-11.
Before claiming any port, check all unit `ExecStart` lines — not just the live socket snapshot.

## mem20 services (systemd)

| Port | Bind | Unit | Serves |
|---|---|---|---|
| 3000 | 0.0.0.0 | `mem20-chat.service` | Open WebUI-style chat front end (`mem20owebz chat`) |
| 4000 | 0.0.0.0 | `mem20-gateway.service` | Model gateway (`mem20owebz serve`) |
| 6667 | 0.0.0.0 | `mem20-ircd.service` | IRC server (ngircd); `mem20botz` and `mem20-dreamer` connect as clients |
| 8000 | 0.0.0.0 | `mem20-messenger.service` | Bot fleet API + WebSocket proxy |
| 8002 | 127.0.0.1 | `mem20googlez-serve.service` | Google ADK-style agent server |
| 8004 | 127.0.0.1 | `mem20mktz-serve.service` | Marketing server (`fs-mkt`) |
| 8005 | 127.0.0.1 | `mem20yetiz.service` | 3D / rigging / mocap pipeline |
| 8006 | 127.0.0.1 | `mem20corez-serve.service` | Model serving / inference |
| 8007 | 127.0.0.1 | `mem20gamez.service` | Game-agent training harness |
| 8085 | 127.0.0.1 | `mem20gamez-harness.service` | Build harness |
| 8221 | 127.0.0.1, [::1] | `mem20-kanban.service` | Kanban board |
| 8766 | 127.0.0.1 | `mem20wasmz-serve.service` | WASM runtime server |
| 8767 | 127.0.0.1 | `mem20webgpuz-serve.service` | WebGPU server |
| 8784 | 127.0.0.1 | `mem20sensorz.service` | Sensor ingest (`fs-sense`) |
| 8791 | 127.0.0.1 | `mem20-temporal.service` | Bi-temporal store |
| 8890 | 127.0.0.1 | `mem20controlz.service` | Control plane |
| 8891 | 127.0.0.1 | `mem20shopz.service` | Shop server |
| 18778 | 0.0.0.0 | `mem20-agentz-desktop.service` | Dashboard (`desktop serve --both`) |
| 18779 | 0.0.0.0 | `mem20-agentz-web.service` | Web gateway + OREO routes (relocated from 18778 by drop-in) |
| 18785 | 0.0.0.0 | `mem20-agentz-desktop.service` | Office / 3D bundle (`--both`) |

`mem20-agentz-desktop` serves two ports because its drop-in
`/etc/systemd/system/mem20-agentz-desktop.service.d/unified.conf` runs `desktop serve --both`.
`mem20-agentz-web` moved to 18779 via `mem20-agentz-web.service.d/relocate.conf` to avoid
the dashboard's 18778. Both overrides are deliberate; do not "fix" the base unit files.

## Docker (compose)

| Host port | Container port | Source | Notes |
|---|---|---|---|
| 9057 | 8080 | `docker-compose.yml` | Host 8080 is owned by `mcp-server.service`; the compose stack publishes on 9057 instead |

## Supporting units (not part of mem20, listed for conflict checking)

| Port | Bind | Unit | Notes |
|---|---|---|---|
| 22 | 0.0.0.0, [::] | `ssh.service` | sshd |
| 1716 | * | — (kdeconnectd) | KDE Connect |
| 4096 | 127.0.0.1 | `bigpickle-brain.service` | opencode |
| 4100 | 127.0.0.1 | `bigpickle-bridge.service` | model bridge |
| 4200 | 0.0.0.0 | `interstice.service` | — |
| 4210 | 127.0.0.1 | `bigpickle-webgateway.service` | mem20agentz webgateway |
| 8080, 8082 | 0.0.0.0 | `mcp-server.service` | MCP HTTP health/metrics + secondary listener |
| 8765 | 127.0.0.1 | `oreo-editor.service` | OREO editor |
| 8781, 8783 | 127.0.0.1 | `user@0.service` | desktop-session apps (unattributed) |
| 8892 | 127.0.0.1 | `scoreboard.service` | scoreboard |
| 9110 | 127.0.0.1 | `cueliez-training-gui.service` | training GUI |
| 11434 | * | `ollama.service` | Ollama |
| 20241, 20242 | 127.0.0.1 | `cloudflared-*.service` | tunnel metrics |
| 35897, 38383 | 127.0.0.1 | `ollama.service` (children) | llama-server instances |
| 42303 | 127.0.0.1 | `containerd.service` | containerd |
| 53310, 43503 | tailscale IPs | `tailscaled.service` | Tailscale |

## Reserved / free

- `9057` — docker compose host mapping (above).
- `8880` — `mem20owebz/tts/docker-compose.tts.yml` (not running; no listener).
- `5173` — Vite dev server default for `/opt/teamz` (not running).

## Allocation rule

A port that is free right now may be claimed by a unit that is not currently listening.
Check every unit's `ExecStart` (including drop-ins) before binding. Never stop, relocate,
or reconfigure a unit you do not own; report it instead.
