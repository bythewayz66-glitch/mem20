"""Shared whiteboard (Excalidraw) for architecture diagrams."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class ElementType(str, Enum):
    """Types of whiteboard elements."""
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    DIAMOND = "diamond"
    ARROW = "arrow"
    LINE = "line"
    TEXT = "text"
    IMAGE = "image"
    FREE_DRAW = "freedraw"
    FRAME = "frame"
    STICKY_NOTE = "sticky_note"


class ElementStyle(BaseModel):
    """Style properties for whiteboard elements."""
    fill: str = "#ffffff"
    stroke: str = "#000000"
    stroke_width: int = 2
    stroke_style: str = "solid"  # solid, dashed, dotted
    fill_style: str = "solid"  # solid, hachure, cross-hatch
    roughness: int = 1
    opacity: float = 1.0
    font_size: int = 20
    font_family: str = "Virgil"  # Virgil, Helvetica, Cascade
    text_align: str = "left"
    background: str = "transparent"


@dataclass
class WhiteboardElement:
    """An element on the whiteboard."""
    id: str
    type: ElementType
    x: float
    y: float
    width: float
    height: float
    angle: float = 0.0
    style: ElementStyle = field(default_factory=ElementStyle)
    text: str = ""  # For text elements
    points: List[List[float]] = field(default_factory=list)  # For lines/arrows
    seed: int = field(default_factory=lambda: int(time.time() * 1000) % 1000000)
    version: int = 1
    version_nonce: int = 0
    is_deleted: bool = False
    group_ids: List[str] = field(default_factory=list)
    frame_id: Optional[str] = None
    bound_elements: List[Dict[str, Any]] = field(default_factory=list)
    link: Optional[str] = None
    locked: bool = False
    custom_data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: str = ""
    updated_by: str = ""

    def to_excalidraw(self) -> Dict[str, Any]:
        """Convert to Excalidraw-compatible format."""
        return {
            "id": self.id,
            "type": self.type.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "angle": self.angle,
            "strokeColor": self.style.stroke,
            "backgroundColor": self.style.fill,
            "fillStyle": self.style.fill_style,
            "strokeWidth": self.style.stroke_width,
            "strokeStyle": self.style.stroke_style,
            "roughness": self.style.roughness,
            "opacity": self.style.opacity,
            "fontSize": self.style.font_size,
            "fontFamily": self.style.font_family,
            "textAlign": self.style.text_align,
            "text": self.text,
            "points": self.points,
            "seed": self.seed,
            "version": self.version,
            "versionNonce": self.version_nonce,
            "isDeleted": self.is_deleted,
            "groupIds": self.group_ids,
            "frameId": self.frame_id,
            "boundElements": self.bound_elements,
            "link": self.link,
            "locked": self.locked,
            "customData": self.custom_data,
        }

    @classmethod
    def from_excalidraw(cls, data: Dict[str, Any]) -> "WhiteboardElement":
        """Create from Excalidraw format."""
        style = ElementStyle(
            fill=data.get("backgroundColor", "#ffffff"),
            stroke=data.get("strokeColor", "#000000"),
            stroke_width=data.get("strokeWidth", 2),
            stroke_style=data.get("strokeStyle", "solid"),
            fill_style=data.get("fillStyle", "solid"),
            roughness=data.get("roughness", 1),
            opacity=data.get("opacity", 1.0),
            font_size=data.get("fontSize", 20),
            font_family=data.get("fontFamily", "Virgil"),
            text_align=data.get("textAlign", "left"),
        )
        return cls(
            id=data["id"],
            type=ElementType(data["type"]),
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            angle=data.get("angle", 0.0),
            style=style,
            text=data.get("text", ""),
            points=data.get("points", []),
            seed=data.get("seed", int(time.time() * 1000) % 1000000),
            version=data.get("version", 1),
            version_nonce=data.get("versionNonce", 0),
            is_deleted=data.get("isDeleted", False),
            group_ids=data.get("groupIds", []),
            frame_id=data.get("frameId"),
            bound_elements=data.get("boundElements", []),
            link=data.get("link"),
            locked=data.get("locked", False),
            custom_data=data.get("customData", {}),
        )


@dataclass
class WhiteboardScene:
    """A whiteboard scene (collection of elements)."""
    id: str
    name: str
    elements: Dict[str, WhiteboardElement] = field(default_factory=dict)
    viewport: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "zoom": 1.0})
    grid_size: int = 20
    theme: str = "light"  # light, dark
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: str = ""
    collaborators: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_element(self, element: WhiteboardElement) -> None:
        self.elements[element.id] = element
        self.updated_at = time.time()

    def remove_element(self, element_id: str) -> bool:
        if element_id in self.elements:
            self.elements[element_id].is_deleted = True
            self.updated_at = time.time()
            return True
        return False

    def get_element(self, element_id: str) -> Optional[WhiteboardElement]:
        return self.elements.get(element_id)

    def to_excalidraw(self) -> Dict[str, Any]:
        """Export to Excalidraw format."""
        return {
            "type": "excalidraw",
            "version": 2,
            "source": "teamz",
            "elements": [e.to_excalidraw() for e in self.elements.values() if not e.is_deleted],
            "appState": {
                "viewBackgroundColor": "#ffffff" if self.theme == "light" else "#1e1e1e",
                "gridSize": self.grid_size,
                "zoom": self.viewport.get("zoom", 1.0),
                "scrollX": self.viewport.get("x", 0),
                "scrollY": self.viewport.get("y", 0),
            },
            "files": {},
        }

    @classmethod
    def from_excalidraw(cls, data: Dict[str, Any], scene_id: str, name: str) -> "WhiteboardScene":
        """Create from Excalidraw format."""
        scene = cls(id=scene_id, name=name)
        for elem_data in data.get("elements", []):
            elem = WhiteboardElement.from_excalidraw(elem_data)
            scene.elements[elem.id] = elem
        return scene


class WhiteboardConfig(BaseModel):
    """Configuration for whiteboard."""
    max_elements_per_scene: int = 5000
    auto_save_interval_seconds: float = 30.0
    history_limit: int = 100
    allow_guest_edit: bool = False
    default_theme: str = "light"
    grid_size: int = 20
    export_formats: List[str] = Field(default_factory=lambda: ["png", "svg", "json", "excalidraw"])


class WhiteboardManager:
    """Manages shared whiteboards."""

    def __init__(
        self,
        config: Optional[WhiteboardConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
    ) -> None:
        self.config = config or WhiteboardConfig()
        self.notifier = notifier
        self._scenes: Dict[str, WhiteboardScene] = {}
        self._user_scenes: Dict[str, Set[str]] = {}  # user_id -> scene_ids
        self._scene_locks: Dict[str, asyncio.Lock] = {}  # scene_id -> lock

    def create_scene(
        self,
        name: str,
        creator: str,
        theme: Optional[str] = None,
    ) -> str:
        """Create a new whiteboard scene."""
        scene_id = str(uuid.uuid4())[:8]

        scene = WhiteboardScene(
            id=scene_id,
            name=name,
            theme=theme or self.config.default_theme,
            created_by=creator,
            collaborators=[creator],
        )

        self._scenes[scene_id] = scene
        self._user_scenes.setdefault(creator, set()).add(scene_id)
        self._scene_locks[scene_id] = asyncio.Lock()

        return scene_id

    def get_scene(self, scene_id: str) -> Optional[WhiteboardScene]:
        """Get a scene by ID."""
        return self._scenes.get(scene_id)

    def list_scenes(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List scenes, optionally filtered by user."""
        if user_id:
            scene_ids = self._user_scenes.get(user_id, set())
            scenes = [self._scenes[sid] for sid in scene_ids if sid in self._scenes]
        else:
            scenes = list(self._scenes.values())

        return [
            {
                "id": s.id,
                "name": s.name,
                "theme": s.theme,
                "element_count": len([e for e in s.elements.values() if not e.is_deleted]),
                "collaborator_count": len(s.collaborators),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in scenes
        ]

    def add_element(
        self,
        scene_id: str,
        element: WhiteboardElement,
        user_id: str,
    ) -> bool:
        """Add an element to a scene."""
        scene = self._scenes.get(scene_id)
        if not scene:
            return False

        if user_id not in scene.collaborators:
            return False

        if len(scene.elements) >= self.config.max_elements_per_scene:
            return False

        element.created_by = user_id
        element.updated_by = user_id
        scene.add_element(element)

        self._notify_scene(scene_id, "element_added", {
            "element": element.to_excalidraw(),
        }, exclude=user_id)

        return True

    def update_element(
        self,
        scene_id: str,
        element_id: str,
        updates: Dict[str, Any],
        user_id: str,
    ) -> bool:
        """Update an element."""
        scene = self._scenes.get(scene_id)
        if not scene:
            return False

        element = scene.get_element(element_id)
        if not element:
            return False

        if element.locked and element.updated_by != user_id:
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(element, key):
                setattr(element, key, value)

        element.version += 1
        element.updated_at = time.time()
        element.updated_by = user_id

        self._notify_scene(scene_id, "element_updated", {
            "element_id": element_id,
            "updates": updates,
        }, exclude=user_id)

        return True

    def delete_element(self, scene_id: str, element_id: str, user_id: str) -> bool:
        """Delete an element."""
        scene = self._scenes.get(scene_id)
        if not scene:
            return False

        element = scene.get_element(element_id)
        if not element:
            return False

        if element.locked and element.created_by != user_id:
            return False

        scene.remove_element(element_id)

        self._notify_scene(scene_id, "element_deleted", {
            "element_id": element_id,
        }, exclude=user_id)

        return True

    def add_collaborator(self, scene_id: str, user_id: str, added_by: str) -> bool:
        """Add a collaborator to a scene."""
        scene = self._scenes.get(scene_id)
        if not scene:
            return False

        if added_by not in scene.collaborators:
            return False

        if user_id not in scene.collaborators:
            scene.collaborators.append(user_id)
            self._user_scenes.setdefault(user_id, set()).add(scene_id)

            self._notify_scene(scene_id, "collaborator_added", {
                "user_id": user_id,
            })

        return True

    def remove_collaborator(self, scene_id: str, user_id: str, removed_by: str) -> bool:
        """Remove a collaborator from a scene."""
        scene = self._scenes.get(scene_id)
        if not scene:
            return False

        if removed_by not in scene.collaborators:
            return False

        if user_id in scene.collaborators:
            scene.collaborators.remove(user_id)
            self._user_scenes.get(user_id, set()).discard(scene_id)

            self._notify_scene(scene_id, "collaborator_removed", {
                "user_id": user_id,
            })

        return True

    def export_scene(self, scene_id: str, format: str = "excalidraw") -> Optional[Dict[str, Any]]:
        """Export a scene in specified format."""
        scene = self._scenes.get(scene_id)
        if not scene:
            return None

        if format == "excalidraw":
            return scene.to_excalidraw()
        elif format == "json":
            return {
                "id": scene.id,
                "name": scene.name,
                "theme": scene.theme,
                "elements": {eid: e.to_excalidraw() for eid, e in scene.elements.items()},
            }
        return None

    def import_scene(
        self,
        data: Dict[str, Any],
        name: str,
        creator: str,
    ) -> str:
        """Import a scene from exported data."""
        scene_id = str(uuid.uuid4())[:8]

        if "elements" in data:
            # JSON format
            scene = WhiteboardScene(id=scene_id, name=name, created_by=creator)
            for elem_data in data["elements"].values():
                elem = WhiteboardElement.from_excalidraw(elem_data)
                scene.elements[elem.id] = elem
        else:
            # Excalidraw format
            scene = WhiteboardScene.from_excalidraw(data, scene_id, name)
            scene.created_by = creator

        scene.collaborators = [creator]
        self._scenes[scene_id] = scene
        self._user_scenes.setdefault(creator, set()).add(scene_id)
        self._scene_locks[scene_id] = asyncio.Lock()

        return scene_id

    def _notify_scene(
        self,
        scene_id: str,
        event: str,
        data: Dict[str, Any],
        exclude: Optional[str] = None,
    ) -> None:
        """Notify all collaborators of a scene event."""
        if not self.notifier:
            return

        scene = self._scenes.get(scene_id)
        if not scene:
            return

        for collaborator in scene.collaborators:
            if collaborator != exclude:
                try:
                    self.notifier(collaborator, f"whiteboard_{event}", {
                        "scene_id": scene_id,
                        **data,
                    })
                except Exception:
                    pass


# Global instance
_whiteboard_manager: Optional[WhiteboardManager] = None


def get_whiteboard(config: Optional[WhiteboardConfig] = None) -> WhiteboardManager:
    """Get global whiteboard manager instance."""
    global _whiteboard_manager
    if _whiteboard_manager is None:
        _whiteboard_manager = WhiteboardManager(config)
    return _whiteboard_manager