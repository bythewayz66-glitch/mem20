extends Node
## Optional autoload entry — create Mem20Client instances as needed.

const Mem20ClientScript = preload("res://addons/mem20/mem20_client.gd")

func create_client() -> RefCounted:
	return Mem20ClientScript.new()
