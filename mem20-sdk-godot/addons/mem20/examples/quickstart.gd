extends Node
## Example: store + recall a grounded fact from a Godot scene.

func _ready() -> void:
	var client := Mem20Client.new()
	client.configure({
		"server_cwd": OS.get_environment("MEM20_ROOT"),
		"timeout_sec": 60.0,
	})

	var err := client.start()
	if err != OK:
		push_error(client.last_error())
		return

	var stored = client.memory_store({
		"content": "NPC Mara will trade herbs for iron",
		"category": "npc",
		"tags": ["mara", "trade"],
		"epistemic_status": "user_stated",
	})
	if typeof(stored) == TYPE_DICTIONARY and stored.has("error"):
		push_error(str(stored["error"]))
		client.close()
		return

	var hits = client.memory_recall({"query": "who trades herbs", "limit": 3})
	print(Mem20Client.text(hits))
	client.close()
