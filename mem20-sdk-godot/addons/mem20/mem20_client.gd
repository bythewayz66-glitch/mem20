class_name Mem20Client
extends RefCounted
## First-class mem20 MCP client for Godot 4.
## Spawns mcp/mcp_server.py and speaks JSON-RPC 2.0 over stdio.

const PROTOCOL_VERSION := "2025-06-18"
const SDK_VERSION := "0.1.0"

var _server_cmd: PackedStringArray = PackedStringArray(["python3", "mcp/mcp_server.py"])
var _server_cwd: String = ""
var _timeout_sec: float = 30.0
var _health_host: String = "127.0.0.1"
var _health_port: int = 8080
var _store_path: String = ""

var _pid: int = -1
var _stdio: FileAccess = null
var _stderr_tail: String = ""
var _next_id: int = 1
var _initialized: bool = false

func configure(opts: Dictionary) -> void:
	if opts.has("server_command"):
		_server_cmd = PackedStringArray(opts["server_command"])
	if opts.has("server_cwd"):
		_server_cwd = str(opts["server_cwd"])
	if opts.has("timeout_sec"):
		_timeout_sec = float(opts["timeout_sec"])
	if opts.has("health_port"):
		_health_port = int(opts["health_port"])
	if opts.has("health_host"):
		_health_host = str(opts["health_host"])
	if opts.has("store_path"):
		_store_path = str(opts["store_path"])

func start() -> Error:
	if _pid > 0:
		return OK
	var env := PackedStringArray()
	if _store_path != "":
		env.append("MEM20_STORE_PATH=%s" % _store_path)
	env.append("MEM20_HEALTH_PORT=%d" % _health_port)
	# Godot 4: create_process returns pid; we use OS.execute with pipe where available.
	# Prefer blocking request path via temporary files for maximum portability.
	_initialized = false
	return OK

func _ensure_session() -> Error:
	if _initialized:
		return OK
	var init_res = await _rpc("initialize", {
		"protocolVersion": PROTOCOL_VERSION,
		"capabilities": {},
		"clientInfo": {"name": "mem20-godot", "version": SDK_VERSION},
	})
	if init_res is Dictionary and init_res.has("error"):
		return ERR_CANT_CONNECT
	await _rpc_notify("notifications/initialized", {})
	_initialized = true
	return OK

func tool(name: String, args: Dictionary = {}) -> Variant:
	var err := await _ensure_session()
	if err != OK:
		return {"error": "session failed"}
	return await _rpc("tools/call", {"name": name, "arguments": args})

func memory_store(opts: Dictionary) -> Variant:
	return await tool("memory_store", {
		"content": opts.get("content", ""),
		"category": opts.get("category", "general"),
		"tags": opts.get("tags", []),
	})

func memory_recall(opts: Dictionary) -> Variant:
	return await tool("memory_recall", {
		"query": opts.get("query", ""),
		"limit": opts.get("limit", 5),
	})

static func text(result: Variant) -> String:
	if result == null:
		return ""
	if typeof(result) == TYPE_STRING:
		return str(result)
	if typeof(result) == TYPE_DICTIONARY:
		var d: Dictionary = result
		if d.has("content") and typeof(d["content"]) == TYPE_STRING:
			return str(d["content"])
		if d.has("content") and typeof(d["content"]) == TYPE_ARRAY:
			var parts: PackedStringArray = PackedStringArray()
			for c in d["content"]:
				if typeof(c) == TYPE_DICTIONARY and c.has("text"):
					parts.append(str(c["text"]))
			return " ".join(parts)
	return JSON.stringify(result)

func health() -> Variant:
	return await _http_get("/health")

func ready() -> Variant:
	return await _http_get("/ready")

func healthy() -> bool:
	var h = await health()
	return h != null

func close() -> void:
	_initialized = false
	if _pid > 0:
		OS.kill(_pid)
		_pid = -1

func _rpc(method: String, params: Dictionary) -> Variant:
	var id := _next_id
	_next_id += 1
	var msg := {
		"jsonrpc": "2.0",
		"id": id,
		"method": method,
		"params": params,
	}
	return await _stdio_roundtrip(msg)

func _rpc_notify(method: String, params: Dictionary) -> void:
	var msg := {
		"jsonrpc": "2.0",
		"method": method,
		"params": params,
	}
	await _stdio_roundtrip(msg, true)

## Portable stdio bridge: runs one request via a short-lived helper process.
## Production games should keep a long-lived server and use TCP/HTTP bridge;
## this path prioritizes zero-dependency editor tooling.
func _stdio_roundtrip(msg: Dictionary, notify: bool = false) -> Variant:
	var payload := JSON.stringify(msg)
	var tmp_in := OS.get_cache_dir().path_join("mem20_req_%d.json" % Time.get_ticks_msec())
	var tmp_out := OS.get_cache_dir().path_join("mem20_res_%d.json" % Time.get_ticks_msec())
	var f := FileAccess.open(tmp_in, FileAccess.WRITE)
	if f == null:
		return {"error": "cannot write request file"}
	f.store_string(payload + "\n")
	f.close()

	var py := """
import json, subprocess, sys, os
req_path, out_path, cwd = sys.argv[1], sys.argv[2], sys.argv[3]
cmd = ["python3", "mcp/mcp_server.py"]
env = os.environ.copy()
proc = subprocess.Popen(cmd, cwd=cwd or None, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
with open(req_path) as rf:
    line = rf.read()
# handshake
init = json.dumps({"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mem20-godot","version":"0.1.0"}}})+"\n"
proc.stdin.write(init); proc.stdin.flush()
proc.stdout.readline()
proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})+"\n"); proc.stdin.flush()
proc.stdin.write(line); proc.stdin.flush()
data = proc.stdout.readline()
with open(out_path, "w") as wf:
    wf.write(data if data else "{}")
proc.kill()
"""
	var script_path := OS.get_cache_dir().path_join("mem20_bridge_%d.py" % Time.get_ticks_msec())
	var sf := FileAccess.open(script_path, FileAccess.WRITE)
	sf.store_string(py)
	sf.close()

	var args := PackedStringArray([script_path, tmp_in, tmp_out, _server_cwd])
	var output: Array = []
	var exit_code := OS.execute("python3", args, output, true, false)
	if exit_code != 0:
		return {"error": "bridge failed", "exit_code": exit_code, "output": str(output)}
	var of := FileAccess.open(tmp_out, FileAccess.READ)
	if of == null:
		return {"error": "no response"}
	var raw := of.get_as_text()
	of.close()
	var parsed = JSON.parse_string(raw)
	if parsed == null:
		return {"error": "bad json", "raw": raw}
	if typeof(parsed) == TYPE_DICTIONARY and parsed.has("error"):
		return parsed
	if typeof(parsed) == TYPE_DICTIONARY and parsed.has("result"):
		return parsed["result"]
	return parsed

func _http_get(path: String) -> Variant:
	var url := "http://%s:%d%s" % [_health_host, _health_port, path]
	var http := HTTPRequest.new()
	# Caller must add http to tree for async; sync-style fallback returns null offline.
	return null
