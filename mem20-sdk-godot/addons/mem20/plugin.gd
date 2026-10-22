@tool
extends EditorPlugin

func _enter_tree() -> void:
	add_autoload_singleton("Mem20", "res://addons/mem20/mem20_autoload.gd")

func _exit_tree() -> void:
	remove_autoload_singleton("Mem20")
