class_name Mem20Client
extends RefCounted
## First-class mem20 MCP client for Godot 4.
##
## Spawns the mem20 MCP server through the committed [code]mem20_bridge.py[/code]
## helper and speaks JSON-RPC 2.0 over stdio. The bridge is one-shot: every
## call starts the server, writes the handshake and request in one batch, and
## returns the matching response. That is the only stdio shape Godot's
## [method OS.execute] can drive without pipe access.

const PROTOCOL_VERSION := "2025-06-18"
const SDK_VERSION := "0.2.0"
const DEFAULT_SERVER_COMMAND := ["python3", "mcp/mcp_server.py"]
const GROUNDED_EPISTEMIC := [
	"observed",
	"inferred",
	"user_stated",
	"hypothesis",
	"agent_generated",
	"unlabeled",
]

var _server_cmd: PackedStringArray = PackedStringArray(DEFAULT_SERVER_COMMAND)
var _server_cwd: String = ""
var _timeout_sec: float = 60.0
var _health_host: String = "127.0.0.1"
var _health_port: int = 8080
var _store_path: String = ""
var _extra_env: Dictionary = {}

var _next_id: int = 1
var _started: bool = false
var _last_error: String = ""

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
	if opts.has("env") and typeof(opts["env"]) == TYPE_DICTIONARY:
		_extra_env = opts["env"]

## Run one real initialize handshake. Calls keep working without this, but
## start() fails fast when the command, checkout or interpreter is wrong.
func start() -> Error:
	if _started:
		return OK
	var request_id := _next_id
	_next_id += 1
	var batch := _request([
		_initialize_message(request_id),
		{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
	])
	var handshake = _extract(batch, request_id)
	if typeof(handshake) != TYPE_DICTIONARY or not handshake.has("protocolVersion"):
		_last_error = str(handshake)
		_started = false
		return ERR_CANT_CONNECT
	_started = true
	_last_error = ""
	return OK

func tool(name: String, args: Dictionary = {}) -> Variant:
	if name.strip_edges() == "":
		return _error("tool name must not be empty")
	return _rpc("tools/call", {"name": name, "arguments": args})

## Store a grounded fact. epistemic_status is required by the tool's own
## inputSchema: omitting it makes the server answer isError=false with an
## explanatory string, which callers mistake for success. Refuse to send it.
func memory_store(opts: Dictionary) -> Variant:
	if not opts.has("content") or str(opts["content"]).strip_edges() == "":
		return _error("content is required for memory_store")

	if not opts.has("epistemic_status") or str(opts["epistemic_status"]).strip_edges() == "":
		return _error(
			"epistemic_status is required for memory_store; declare how the claim is known "
			+ "(observed, inferred, user_stated, hypothesis, agent_generated, unlabeled)"
		)

	var status := str(opts["epistemic_status"]).strip_edges()
	if status == "imagined":
		return _error(
			"'imagined' is not a grounded epistemic_status: invented content belongs in the "
			+ "simulated partition. Use memory_simulate_store."
		)
	if not GROUNDED_EPISTEMIC.has(status):
		return _error(
			"unknown epistemic_status '%s' (expected one of: %s)"
			% [status, ", ".join(GROUNDED_EPISTEMIC)]
		)

	var tags = opts.get("tags", "")
	var tag_text := ""
	if typeof(tags) == TYPE_ARRAY:
		var parts := PackedStringArray()
		for tag in tags:
			parts.append(str(tag))
		tag_text = ",".join(parts)
	else:
		tag_text = str(tags)

	return tool("memory_store", {
		"content": str(opts["content"]),
		"category": str(opts.get("category", "general")),
		"tags": tag_text,
		"epistemic_status": status,
	})

func memory_recall(opts: Dictionary) -> Variant:
	var args := {
		"query": str(opts.get("query", "")),
		"limit": int(opts.get("limit", 5)),
	}
	if opts.has("category") and str(opts["category"]) != "":
		args["category"] = str(opts["category"])
	return tool("memory_recall", args)

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
			var parts := PackedStringArray()
			for c in d["content"]:
				if typeof(c) == TYPE_DICTIONARY and c.has("text"):
					parts.append(str(c["text"]))
			return "\n".join(parts)
		if d.has("error"):
			return "error: %s" % str(d["error"])
	return JSON.stringify(result)

## GET /health on the server's health endpoint. Returns the decoded body, or
## null when the endpoint is unreachable (for example when it is disabled).
func health() -> Variant:
	return await _http_get("/health")

## GET /ready on the server's readiness endpoint. Same contract as health().
func ready() -> Variant:
	return await _http_get("/ready")

func healthy() -> bool:
	var result = await health()
	if result == null:
		return false
	if typeof(result) == TYPE_DICTIONARY and result.has("error"):
		return false
	return true

## Releases client state. The bridge process itself is short-lived per call,
## so there is no child process left to kill.
func close() -> void:
	_started = false
	_next_id = 1

func last_error() -> String:
	return _last_error

func _initialize_message(request_id: int) -> Dictionary:
	return {
		"jsonrpc": "2.0",
		"id": request_id,
		"method": "initialize",
		"params": {
			"protocolVersion": PROTOCOL_VERSION,
			"capabilities": {},
			"clientInfo": {"name": "mem20-godot", "version": SDK_VERSION},
		},
	}

func _rpc(method: String, params: Dictionary) -> Variant:
	var request_id := _next_id
	_next_id += 1
	var batch := _request([
		_initialize_message(0),
		{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
		{"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
	])
	return _extract(batch, request_id)

func _extract(batch: Dictionary, request_id: int) -> Variant:
	if batch.has("error"):
		return batch
	var responses: Dictionary = batch.get("responses", {})
	var key := str(request_id)
	if not responses.has(key):
		return {
			"error": "server returned no response for request %s" % key,
			"bridge": batch,
		}
	var envelope = responses[key]
	if typeof(envelope) != TYPE_DICTIONARY:
		return {"error": "malformed JSON-RPC response", "bridge": batch}
	if envelope.has("error"):
		return {"error": envelope["error"]}
	return envelope.get("result", {})

func _request(messages: Array) -> Dictionary:
	var bridge_path := _bridge_path()
	if bridge_path == "":
		return _error("mem20_bridge.py is missing next to mem20_client.gd")

	var workspace := _workspace()
	if workspace == "":
		return _error(
			"cannot create the mem20 bridge workspace under %s" % OS.get_user_data_dir()
		)

	var stamp := "%d_%d" % [Time.get_ticks_usec(), randi()]
	var request_path := workspace.path_join("request_%s.json" % stamp)
	var response_path := workspace.path_join("response_%s.json" % stamp)
	var request := {
		"server_command": Array(_resolve_server_command()),
		"cwd": _server_cwd,
		"env": _base_env(),
		"timeout_sec": _timeout_sec,
		"messages": messages,
	}

	var handle := FileAccess.open(request_path, FileAccess.WRITE)
	if handle == null:
		return _error(
			"cannot write bridge request: %s" % error_string(FileAccess.get_open_error())
		)
	handle.store_string(JSON.stringify(request))
	handle.close()

	var output: Array = []
	var exit_code := OS.execute(
		_bridge_python(),
		PackedStringArray([bridge_path, request_path, response_path]),
		output,
		true,
		false
	)

	var response_text := ""
	var reader := FileAccess.open(response_path, FileAccess.READ)
	if reader != null:
		response_text = reader.get_as_text()
		reader.close()

	DirAccess.remove_absolute(request_path)
	DirAccess.remove_absolute(response_path)

	if response_text == "":
		return _error(
			"bridge produced no response (exit %d): %s"
			% [exit_code, " ".join(PackedStringArray(output))]
		)

	var parsed = JSON.parse_string(response_text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return _error("bridge response is not valid JSON: %s" % response_text.substr(0, 500))
	return parsed

func _resolve_server_command() -> PackedStringArray:
	var command := PackedStringArray(_server_cmd)
	if command.is_empty():
		command = PackedStringArray(DEFAULT_SERVER_COMMAND)
	if command.size() > 0 and _server_cwd != "":
		# Only auto-detect the venv for a bare interpreter name. An explicit
		# path such as /usr/bin/python3 is the caller's choice and is honoured.
		var executable := command[0]
		var bare := executable == executable.get_file()
		var first := executable.get_file().to_lower()
		if bare and (first == "python" or first == "python3" or first.begins_with("python3.")):
			var venv := _venv_python()
			if venv != "":
				command[0] = venv
	return command

func _bridge_python() -> String:
	var venv := _venv_python()
	if venv != "":
		return venv
	return "python" if OS.get_name() == "Windows" else "python3"

func _venv_python() -> String:
	if _server_cwd == "":
		return ""
	var relative := ".venv/Scripts/python.exe" if OS.get_name() == "Windows" else ".venv/bin/python"
	var candidate := _server_cwd.path_join(relative)
	if FileAccess.file_exists(candidate):
		return candidate
	return ""

func _bridge_path() -> String:
	var script := get_script()
	if script != null and script.resource_path != "":
		var beside_script: String = script.resource_path.get_base_dir().path_join("mem20_bridge.py")
		if FileAccess.file_exists(beside_script):
			return ProjectSettings.globalize_path(beside_script)
	var fallback := "res://addons/mem20/mem20_bridge.py"
	if FileAccess.file_exists(fallback):
		return ProjectSettings.globalize_path(fallback)
	return ""

func _workspace() -> String:
	var directory := OS.get_user_data_dir().path_join("mem20_bridge")
	var err := DirAccess.make_dir_recursive_absolute(directory)
	if err != OK and err != ERR_ALREADY_EXISTS:
		return ""
	return directory

func _base_env() -> Dictionary:
	var env := {}
	for key in _extra_env:
		env[str(key)] = str(_extra_env[key])
	if _store_path != "":
		env["MEM20_STORE_PATH"] = _store_path
	env["MEM20_HEALTH_PORT"] = str(_health_port)
	return env

func _http_get(path: String) -> Variant:
	var loop := Engine.get_main_loop()
	if loop == null or not (loop is SceneTree):
		return null
	var root := (loop as SceneTree).root
	if root == null:
		return null

	var url := "http://%s:%d%s" % [_health_host, _health_port, path]
	var http := HTTPRequest.new()
	http.timeout = _timeout_sec
	# add_child() fails while the parent is still setting up children, which is
	# exactly where a caller's _ready() runs. Wait for the root Window to finish
	# its own setup before attaching the request node.
	if not root.is_node_ready():
		await root.ready
	root.add_child(http)
	if not http.is_inside_tree():
		http.queue_free()
		return null
	var err := http.request(url)
	if err != OK:
		http.queue_free()
		return null

	var completed: Array = await http.request_completed
	http.queue_free()

	var transport_result: int = completed[0]
	var status: int = completed[1]
	var body: PackedByteArray = completed[3]
	if transport_result != HTTPRequest.RESULT_SUCCESS:
		return null

	var text_body := body.get_string_from_utf8()
	var parsed = JSON.parse_string(text_body)
	if status < 200 or status >= 300:
		if typeof(parsed) == TYPE_DICTIONARY:
			parsed["http_status"] = status
			parsed["error"] = "HTTP %d" % status
			return parsed
		return {"error": "HTTP %d" % status, "url": url, "body": text_body}
	if typeof(parsed) == TYPE_DICTIONARY or typeof(parsed) == TYPE_ARRAY:
		return parsed
	return {"status": "ok", "url": url, "body": text_body}

static func _error(message: String) -> Dictionary:
	return {"error": message}
