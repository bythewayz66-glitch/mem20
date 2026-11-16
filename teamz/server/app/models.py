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
