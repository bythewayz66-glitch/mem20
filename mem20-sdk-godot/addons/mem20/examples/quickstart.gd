extends Node
## Example: store + recall a grounded fact from a Godot scene.

func _ready() -> void:
	var client := Mem20Client.new()
	client.configure({
		"server_cwd": OS.get_environment("MEM20_ROOT"),
		"timeout_sec": 60.0,
	})
	await client.start()
	await client.memory_store({
		"content": "NPC Mara will trade herbs for iron",
		"category": "npc",
		"tags": ["mara", "trade"],
	})
	var hits = await client.memory_recall({"query": "who trades herbs", "limit": 3})
	print(Mem20Client.text(hits))
	client.close()
