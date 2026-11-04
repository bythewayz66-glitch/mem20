extends Node
## Headless round-trip test for the mem20 Godot addon.
##
## Run through tests/run_headless.sh, which builds a throwaway project, starts
## the health fixture and points MEM20_ROOT at a real mem20 checkout.

var failures: int = 0

func _ready() -> void:
	await _run()
	get_tree().quit(1 if failures > 0 else 0)

func _check(name: String, condition: bool, detail: String = "") -> void:
	if condition:
		print("PASS %s" % name)
	else:
		failures += 1
		print("FAIL %s%s" % [name, "" if detail == "" else ": " + detail])

func _run() -> void:
	var root := OS.get_environment("MEM20_ROOT")
	var health_port := int(OS.get_environment("MEM20_TEST_HEALTH_PORT"))
	var store_path := OS.get_environment("MEM20_TEST_STORE")
	_check("MEM20_ROOT is set", root != "", root)
	_check("MEM20_TEST_HEALTH_PORT is set", health_port > 0, str(health_port))

	var client := Mem20Client.new()
	client.configure({
		"server_cwd": root,
		"timeout_sec": 120.0,
		"health_host": "127.0.0.1",
		"health_port": health_port,
		"store_path": store_path,
	})

	var start_result := client.start()
	_check("start() handshake", start_result == OK, client.last_error())

	var health = await client.health()
	_check(
		"health() decodes HTTP JSON",
		typeof(health) == TYPE_DICTIONARY and str(health.get("service", "")) == "mem20",
		JSON.stringify(health)
	)

	var ready = await client.ready()
	_check(
		"ready() decodes HTTP JSON",
		typeof(ready) == TYPE_DICTIONARY and bool(ready.get("ready", false)),
		JSON.stringify(ready)
	)
	_check("healthy() is true against a live endpoint", await client.healthy())

	var status = client.tool("memory_status", {})
	_check(
		"tool(memory_status) round-trip",
		typeof(status) == TYPE_DICTIONARY and not status.has("error") and status.has("content"),
		JSON.stringify(status)
	)

	var missing = client.memory_store({"content": "refused without a status"})
	_check(
		"memory_store rejects a missing epistemic_status",
		typeof(missing) == TYPE_DICTIONARY and missing.has("error"),
		JSON.stringify(missing)
	)

	var imagined = client.memory_store({
		"content": "an invented fact",
		"epistemic_status": "imagined",
	})
	_check(
		"memory_store rejects an imagined status",
		typeof(imagined) == TYPE_DICTIONARY and imagined.has("error"),
		JSON.stringify(imagined)
	)

	var stored = client.memory_store({
		"content": "Godot round-trip probe at %d" % Time.get_unix_time_from_system(),
		"epistemic_status": "observed",
		"category": "tool",
		"tags": ["godot", "probe"],
	})
	_check(
		"memory_store accepts a grounded status",
		typeof(stored) == TYPE_DICTIONARY
			and not stored.has("error")
			and not bool(stored.get("isError", false)),
		JSON.stringify(stored)
	)

	var bad_command := Mem20Client.new()
	bad_command.configure({
		"server_command": ["definitely-not-a-real-mem20-binary", "mcp/mcp_server.py"],
		"server_cwd": root,
		"timeout_sec": 5.0,
	})
	_check(
		"server_command is honoured",
		bad_command.start() != OK and bad_command.last_error().find("not found") >= 0,
		bad_command.last_error()
	)

	client.close()
