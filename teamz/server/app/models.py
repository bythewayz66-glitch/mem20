from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] = "user"
    content: Any = ""
    name: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class AttemptInfo(BaseModel):
    provider: str
    model: Optional[str] = None
    status: Literal["started", "success", "failed", "skipped"]
    latency_ms: Optional[int] = None
    reason: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[Usage] = None
    keyless: Optional[bool] = None


class RoutingMeta(BaseModel):
    selected_provider: Optional[str] = None
    selected_model: Optional[str] = None
    attempts: List[AttemptInfo] = Field(default_factory=list)
    fallback_used: bool = False
    requested_model: Optional[str] = None


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    # Teamz-specific context
    agent: Optional[Dict[str, Any]] = None
    conversation: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    # When true, treat agent/model as preference, never hard filter that can cause outage
    strict_model: bool = False


class ChatChoice(BaseModel):
    index: int = 0
    message: Dict[str, Any]
    finish_reason: Optional[str] = "stop"


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Optional[Usage] = None
    routing: Optional[RoutingMeta] = None


class OptimizePromptRequest(BaseModel):
    draft: str
    conversation: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    channel: Optional[Dict[str, Any]] = None
    goal: Optional[str] = None
    memory_query: Optional[str] = None
    use_memory: bool = True
    stream: bool = False


class OptimizePromptResponse(BaseModel):
    prompt: str
    original: str
    memories_used: List[Dict[str, Any]] = Field(default_factory=list)
    routing: Optional[RoutingMeta] = None


class MemoryRecallRequest(BaseModel):
    query: str
    limit: int = 5


class MemoryStoreRequest(BaseModel):
    content: str
    category: str = "teamz"
    tags: Any = None


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


# --- Persistence / rooms / goals -----------------------------------------

class Goal(BaseModel):
    text: str
    active: bool = True
    done: bool = False
    status: str = "active"
    progress: int = 0
    steps: int = 0
    lastStep: Optional[str] = None
    nextStep: Optional[str] = None
    lastError: Optional[str] = None
    lastAgentId: Optional[str] = None
    createdAt: int = 0
    updatedAt: Optional[int] = None
    cooldownUntil: Optional[float] = None


class Task(BaseModel):
    id: str
    conversationId: Optional[str] = None
    agentId: Optional[str] = None
    title: str
    status: str = "todo"  # todo | doing | blocked | done
    goal: Optional[str] = None
    createdAt: int = 0
    updatedAt: Optional[int] = None


class ActivityEvent(BaseModel):
    id: str
    conversationId: Optional[str] = None
    agentId: Optional[str] = None
    agentName: Optional[str] = None
    kind: str = "info"
    text: str = ""
    progress: Optional[int] = None
    tools: List[str] = Field(default_factory=list)
    at: int = 0


class WorkspaceSnapshot(BaseModel):
    """The whole persisted workspace/session state."""
    version: int = 1
    updatedAt: Optional[int] = None
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    conversations: List[Dict[str, Any]] = Field(default_factory=list)
    messages: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    filters: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    activeConversationId: Optional[str] = None
    goals: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    activity: List[Dict[str, Any]] = Field(default_factory=list)


class SetGoalRequest(BaseModel):
    conversationId: str
    text: str
    active: bool = True


class TerminalExecRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: Optional[float] = None
    agentId: Optional[str] = None


class FileReadRequest(BaseModel):
    path: str
    offset: Optional[int] = 0
    limit: Optional[int] = 2000


class FileWriteRequest(BaseModel):
    path: str
    content: str
    append: bool = False


class FileEditRequest(BaseModel):
    path: str
    old_string: str
    new_string: str
    replace_all: bool = False


class FileListRequest(BaseModel):
    path: Optional[str] = "."


class RuntimeAction(BaseModel):
    tool: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    args: Optional[Dict[str, Any]] = None


class RuntimeExecRequest(BaseModel):
    actions: List[RuntimeAction] = Field(default_factory=list)
    agentId: Optional[str] = None


class WorkerControlRequest(BaseModel):
    action: str  # start | stop | tick | self-improve
    conversationId: Optional[str] = None
    agentId: Optional[str] = None


# --- Phase 5: Skill System & Agent Growth ------------------------------------

class AgentSkill(BaseModel):
    """A skill as stored on an agent."""
    key: str
    label: str
    level: int  # 1-5
    xp: int = 0
    total_xp_for_level: int = 100  # XP needed to reach next level


class AgentSkillProgress(BaseModel):
    """Tracks XP progress for a specific skill."""
    agent_id: str
    skill_key: str
    xp: int = 0
    level: int = 1
    total_xp_earned: int = 0
    last_updated: int = 0


class SkillTreeNode(BaseModel):
    """A node in the skill tree with prerequisites."""
    key: str
    label: str
    description: str
    category: str
    max_level: int = 5
    prerequisites: List[str] = Field(default_factory=list)  # skill keys required
    xp_per_level: int = 100


class AgentSkillCertificate(BaseModel):
    """A certificate earned when an agent masters a skill."""
    id: str
    agent_id: str
    skill_key: str
    skill_label: str
    level_achieved: int
    earned_at: int
    certificate_hash: str  # For verification


class SkillMarketplaceListing(BaseModel):
    """A skill package available in the marketplace."""
    id: str
    author_agent_id: str
    author_agent_name: str
    skill_key: str
    skill_label: str
    description: str
    category: str
    price_xp: int  # Cost in XP to acquire
    min_level: int = 1
    tags: List[str] = Field(default_factory=list)
    created_at: int
    downloads: int = 0
    rating: float = 0.0


class MentorSession(BaseModel):
    """A mentoring session between two agents."""
    id: str
    mentor_agent_id: str
    mentee_agent_id: str
    skill_key: str
    status: Literal["pending", "active", "completed", "cancelled"] = "pending"
    started_at: int
    completed_at: Optional[int] = None
    xp_transferred: int = 0
    notes: str = ""


class SkillDecayConfig(BaseModel):
    """Configuration for skill proficiency decay."""
    enabled: bool = True
    decay_rate_per_day: float = 0.01  # 1% per day
    min_level_before_decay: int = 2  # Don't decay below this level
    decay_interval_hours: int = 24


# --- Phase 6: Multi-Room Orchestration -------------------------------------

class RoomDependency(BaseModel):
    """A dependency between rooms (rooms that must complete before others can start)."""
    room_id: str
    depends_on: List[str] = Field(default_factory=list)  # Room IDs that must complete first
    dependency_type: Literal["blocking", "soft"] = "blocking"  # blocking = must complete, soft = preferred


class RoomTemplate(BaseModel):
    """A template for creating rooms with predefined structure."""
    id: str
    name: str
    description: str
    category: str  # e.g., "development", "research", "design", "operations"
    agent_roles: List[str] = Field(default_factory=list)  # Required agent roles
    required_skills: List[str] = Field(default_factory=list)  # Required skill keys
    default_topic: Optional[str] = None
    default_step_budget: int = 50
    default_tick_s: float = 60.0
    created_at: int


class ProjectRoom(BaseModel):
    """A parent project containing multiple child rooms."""
    id: str
    name: str
    description: str
    parent_room_id: Optional[str] = None  # For nested projects
    child_room_ids: List[str] = Field(default_factory=list)
    status: Literal["planning", "active", "paused", "completed", "archived"] = "planning"
    dependencies: List[RoomDependency] = Field(default_factory=list)
    shared_artifacts: Dict[str, str] = Field(default_factory=dict)  # artifact_name -> storage_path
    created_at: int
    updated_at: int
    completed_at: Optional[int] = None
    template_id: Optional[str] = None


class ArtifactStoreEntry(BaseModel):
    """An artifact stored in the shared artifact store."""
    id: str
    name: str
    description: str
    content_type: str  # e.g., "code", "document", "image", "binary", "log"
    content: str  # Base64 encoded or text
    size_bytes: int
    tags: List[str] = Field(default_factory=list)
    created_by: str  # agent_id or "system"
    room_id: Optional[str] = None  # Which room created it
    project_id: Optional[str] = None  # Which project it belongs to
    created_at: int
    updated_at: int
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkerPoolEntry(BaseModel):
    """An agent in the global worker pool."""
    agent_id: str
    name: str
    role: str
    skills: List[str] = Field(default_factory=list)  # skill keys
    status: Literal["available", "busy", "offline", "maintenance"] = "available"
    current_room_id: Optional[str] = None
    current_task: Optional[str] = None
    max_concurrent_tasks: int = 1
    current_tasks: int = 0
    last_active: int
    assigned_at: Optional[int] = None


class RoomMessageBusMessage(BaseModel):
    """A message on the cross-room message bus."""
    id: str
    from_room_id: str
    to_room_id: Optional[str] = None  # None = broadcast to all
    message_type: str  # "notification", "request", "response", "artifact", "status"
    payload: Dict[str, Any]
    priority: int = 0  # Higher = more urgent
    requires_response: bool = False
    correlation_id: Optional[str] = None  # For request/response correlation
    created_at: int
    ttl_seconds: int = 3600  # Time to live


class CrossRoomEvent(BaseModel):
    """An event that can trigger actions in other rooms."""
    id: str
    event_type: str  # "room_completed", "artifact_created", "goal_achieved", "milestone_reached"
    source_room_id: str
    source_agent_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: int
    propagated: bool = False
