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


class RouteContext(BaseModel):
    """Context for LLM routing decisions."""
    conversationKind: Optional[Literal["direct", "channel"]] = None
    conversationName: Optional[str] = None
    topic: Optional[str] = None
    otherAgents: Optional[List[Dict[str, str]]] = None
    directed: Optional[bool] = None
    conversationId: Optional[str] = None
    workspace: Optional[Dict[str, Any]] = None


# --- Phase 7: Testing & Quality Gates ----------------------------------------

class TestFile(BaseModel):
    """A test file in the workspace."""
    id: str
    path: str
    language: str  # e.g., "python", "typescript", "javascript"
    test_framework: str  # e.g., "pytest", "vitest", "jest", "go test"
    created_at: int
    updated_at: int
    coverage_pct: float = 0.0


class TestRun(BaseModel):
    """A single test run result."""
    id: str
    test_file_id: str
    room_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: Literal["passed", "failed", "skipped", "flaky"] = "skipped"
    duration_ms: int = 0
    coverage_pct: float = 0.0
    output: str = ""
    error: Optional[str] = None
    started_at: int
    completed_at: Optional[int] = None


class CoverageReport(BaseModel):
    """Coverage report for a room or project."""
    id: str
    room_id: Optional[str] = None
    project_id: Optional[str] = None
    total_lines: int = 0
    covered_lines: int = 0
    coverage_pct: float = 0.0
    threshold_pct: float = 80.0
    gate_passed: bool = False
    generated_at: int


class MutationTestResult(BaseModel):
    """Result of a mutation test run."""
    id: str
    test_file_id: str
    room_id: Optional[str] = None
    total_mutants: int = 0
    killed_mutants: int = 0
    survived_mutants: int = 0
    timeout_mutants: int = 0
    error_mutants: int = 0
    mutation_score: float = 0.0  # killed / total
    threshold_pct: float = 80.0
    gate_passed: bool = False
    started_at: int
    completed_at: Optional[int] = None


class ContractTestResult(BaseModel):
    """Result of contract testing against OpenAPI schema."""
    id: str
    endpoint: str
    method: str
    schema_valid: bool = False
    request_valid: bool = False
    response_valid: bool = False
    errors: List[str] = Field(default_factory=list)
    tested_at: int


class VisualRegressionResult(BaseModel):
    """Result of visual regression testing."""
    id: str
    test_name: str
    room_id: Optional[str] = None
    baseline_screenshot: str  # base64
    current_screenshot: str  # base64
    diff_screenshot: Optional[str] = None
    diff_pixels: int = 0
    diff_pct: float = 0.0
    threshold_pct: float = 0.1
    passed: bool = True
    tested_at: int


class PerformanceBenchmark(BaseModel):
    """Performance benchmark result."""
    id: str
    name: str
    room_id: Optional[str] = None
    metric: str  # "latency_p50", "latency_p95", "latency_p99", "throughput", "memory_mb", "cpu_pct"
    value: float
    unit: str
    baseline_value: Optional[float] = None
    regression_pct: Optional[float] = None
    threshold_pct: float = 10.0
    regression_detected: bool = False
    measured_at: int


class SecurityScanResult(BaseModel):
    """Result of a security scan."""
    id: str
    tool: str  # "semgrep", "trivy", "zap", "bandit"
    room_id: Optional[str] = None
    project_id: Optional[str] = None
    severity: Literal["critical", "high", "medium", "low", "info"]
    finding: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    description: str
    remediation: Optional[str] = None
    scanned_at: int


class DependencyAuditResult(BaseModel):
    """Result of a dependency audit."""
    id: str
    room_id: Optional[str] = None
    project_id: Optional[str] = None
    package_manager: str  # "npm", "pip", "cargo", "go", "maven"
    package_name: str
    current_version: str
    latest_version: str
    update_type: Literal["patch", "minor", "major", "security"]
    cve_ids: List[str] = Field(default_factory=list)
    auto_pr_created: bool = False
    pr_url: Optional[str] = None
    audited_at: int


class FlakyTestDetection(BaseModel):
    """Flaky test detection result."""
    id: str
    test_file_id: str
    room_id: Optional[str] = None
    test_name: str
    flaky_score: float  # 0-1, higher = more flaky
    runs_analyzed: int
    pass_rate: float
    detection_method: str  # "repeated_runs", "historical_analysis"
    detected_at: int


class QualityDashboardEntry(BaseModel):
    """An entry in the quality dashboard."""
    id: str
    room_id: str
    metric_type: str  # "test_health", "coverage", "mutation_score", "flaky_tests", "security", "performance"
    value: float
    threshold: float
    status: Literal["healthy", "warning", "critical", "unknown"] = "unknown"
    trend: Literal["improving", "stable", "degrading", "unknown"] = "unknown"
    measured_at: int


class DeadLetterActionRequest(BaseModel):
    entry_id: str
    action: str  # retry | resolve | dismiss
    resolution_note: Optional[str] = None


class QualityGateConfig(BaseModel):
    """Configuration for quality gates."""
    coverage_threshold: float = 80.0
    mutation_threshold: float = 80.0
    performance_regression_threshold: float = 10.0
    visual_regression_threshold: float = 0.1
    mutation_timeout_seconds: int = 30
    flaky_test_runs: int = 5
    coverage_required_for_done: bool = True


# --- Phase 8: Observability & Debugging ------------------------------------

class TelemetrySpan(BaseModel):
    """A single span in a distributed trace."""
    id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    operation_name: str  # "goal", "step", "tool", "llm_call"
    start_time: int  # microseconds since epoch
    end_time: Optional[int] = None
    duration_ms: Optional[int] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["ok", "error", "cancelled"] = "ok"
    error_message: Optional[str] = None


class TelemetryTrace(BaseModel):
    """A complete distributed trace."""
    trace_id: str
    root_span_id: str
    spans: List[TelemetrySpan] = Field(default_factory=list)
    start_time: int
    end_time: Optional[int] = None
    room_id: Optional[str] = None
    goal_id: Optional[str] = None
    agent_id: Optional[str] = None


class TokenUsageRecord(BaseModel):
    """Token usage for cost tracking."""
    id: str
    room_id: str
    agent_id: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: int
    span_id: Optional[str] = None


class CostBudget(BaseModel):
    """Cost budget for a room/project/org."""
    id: str
    scope: Literal["room", "project", "org"]
    scope_id: str
    budget_usd: float
    spent_usd: float = 0.0
    period_start: int
    period_end: int
    alert_threshold_pct: float = 80.0
    hard_stop: bool = False


class AlertRule(BaseModel):
    """Alert rule for monitoring."""
    id: str
    name: str
    condition: str  # e.g., "goal_stalled > 300", "error_rate > 0.1", "cost > budget * 0.8"
    severity: Literal["info", "warning", "critical"] = "warning"
    enabled: bool = True
    cooldown_seconds: int = 300
    notification_channels: List[str] = Field(default_factory=list)


class AlertEvent(BaseModel):
    """A triggered alert event."""
    id: str
    rule_id: str
    room_id: Optional[str] = None
    message: str
    severity: Literal["info", "warning", "critical"]
    triggered_at: int
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[int] = None
    resolved_at: Optional[int] = None


class AuditLogEntry(BaseModel):
    """Immutable audit log entry."""
    id: str
    timestamp: int
    actor_id: str  # agent_id, user_id, or "system"
    actor_type: Literal["agent", "user", "system"]
    action: str  # e.g., "tool_call", "goal_created", "agent_spawned", "config_changed"
    resource_type: str  # "room", "agent", "goal", "artifact", "config"
    resource_id: str
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    signature: str  # cryptographic signature for immutability
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReplaySnapshot(BaseModel):
    """Snapshot for deterministic replay."""
    id: str
    trace_id: str
    seed: str
    step: int
    state_hash: str  # hash of the entire state at this step
    prompt: str
    context: Dict[str, Any]
    created_at: int


class TimelineEvent(BaseModel):
    """Event for Gantt timeline view."""
    id: str
    room_id: str
    agent_id: str
    agent_name: str
    event_type: Literal["step_start", "step_end", "tool_call", "llm_call", "waiting", "error"]
    start_time: int
    end_time: Optional[int] = None
    duration_ms: Optional[int] = None
    label: str
    details: Dict[str, Any] = Field(default_factory=dict)
    color: Optional[str] = None


class ObservabilityConfig(BaseModel):
    """Configuration for observability features."""
    tracing_enabled: bool = True
    tracing_sample_rate: float = 1.0
    otlp_endpoint: Optional[str] = None
    token_tracking_enabled: bool = True
    cost_tracking_enabled: bool = True
    audit_log_enabled: bool = True
    replay_enabled: bool = True
    replay_retention_days: int = 30
    alerting_enabled: bool = True
    audit_log_signing_key: Optional[str] = None


class TraceExportRequest(BaseModel):
    """Request to export traces."""
    trace_ids: Optional[List[str]] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    format: Literal["jaeger", "zipkin", "tempo", "json"] = "json"
    include_spans: bool = True


class AlertingConfig(BaseModel):
    """Configuration for alerting."""
    enabled: bool = True
    default_cooldown_seconds: int = 300
    notification_webhook: Optional[str] = None
    slack_webhook: Optional[str] = None
    email_recipients: List[str] = Field(default_factory=list)


# Request/Response models for Phase 8 API
class GetTraceRequest(BaseModel):
    trace_id: str


class GetTracesRequest(BaseModel):
    room_id: Optional[str] = None
    goal_id: Optional[str] = None
    agent_id: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    limit: int = 50
    offset: int = 0


class GetTokenUsageRequest(BaseModel):
    room_id: Optional[str] = None
    agent_id: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    limit: int = 100
    offset: int = 0


class GetCostBudgetRequest(BaseModel):
    scope: Literal["room", "project", "org"]
    scope_id: str


class CreateCostBudgetRequest(BaseModel):
    scope: Literal["room", "project", "org"]
    scope_id: str
    budget_usd: float
    period_start: int
    period_end: int
    alert_threshold_pct: float = 80.0
    hard_stop: bool = False


class CreateAlertRuleRequest(BaseModel):
    name: str
    condition: str
    severity: Literal["info", "warning", "critical"] = "warning"
    enabled: bool = True
    cooldown_seconds: int = 300
    notification_channels: List[str] = Field(default_factory=list)


class AcknowledgeAlertRequest(BaseModel):
    alert_id: str
    acknowledged_by: str


class GetAuditLogRequest(BaseModel):
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    limit: int = 100
    offset: int = 0


class WorkerLogQuery(BaseModel):
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    kind: Optional[str] = None
    from_at: Optional[int] = None
    to_at: Optional[int] = None
    limit: int = 100
    offset: int = 0


class GetReplayRequest(BaseModel):
    trace_id: str
    step: Optional[int] = None


class GetTimelineRequest(BaseModel):
    room_id: str
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    agent_id: Optional[str] = None
    limit: int = 200


class ExportTracesRequest(BaseModel):
    trace_ids: Optional[List[str]] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    format: Literal["jaeger", "zipkin", "tempo", "json"] = "json"
    include_spans: bool = True


class ObservabilityConfigRequest(BaseModel):
    tracing_enabled: Optional[bool] = None
    tracing_sample_rate: Optional[float] = None
    otlp_endpoint: Optional[str] = None
    token_tracking_enabled: Optional[bool] = None
    cost_tracking_enabled: Optional[bool] = None
    audit_log_enabled: Optional[bool] = None
    replay_enabled: Optional[bool] = None
    replay_retention_days: Optional[int] = None
    alerting_enabled: Optional[bool] = None


# --- Phase 9: LLM Provider Ecosystem ----------------------------------------

class LLMProviderConfig(BaseModel):
    """Configuration for an LLM provider."""
    id: str
    name: str
    provider_type: Literal["openai", "anthropic", "ollama", "llamacpp", "vllm", "tgi", "pollinations", "llm7", "ovhcloud", "custom"]
    base_url: str
    api_key: Optional[str] = None
    api_key_env: Optional[str] = None  # Environment variable name for BYOK
    models: List[str] = Field(default_factory=list)
    enabled: bool = True
    priority: int = 100  # Lower = higher priority
    timeout_s: float = 60.0
    max_retries: int = 3
    keyless: bool = False
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    max_context_tokens: int = 4096
    default_model: Optional[str] = None
    prompt_template: Optional[str] = None  # Provider-specific prompt template
    cost_per_1k_prompt_tokens: float = 0.0
    cost_per_1k_completion_tokens: float = 0.0
    headers: Dict[str, str] = Field(default_factory=dict)
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class ProviderHealthStatus(BaseModel):
    """Health status for a provider."""
    provider_id: str
    provider_name: str
    status: Literal["healthy", "degraded", "unhealthy", "unknown"]
    latency_ms: Optional[float] = None
    error_rate: float = 0.0
    success_rate: float = 1.0
    last_check: int
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    cost_per_1k_tokens: float = 0.0


class ProviderFailoverConfig(BaseModel):
    """Configuration for automatic failover."""
    enabled: bool = True
    max_failover_attempts: int = 3
    health_check_interval_seconds: int = 60
    failover_threshold_error_rate: float = 0.5
    failover_threshold_latency_ms: float = 30000.0
    cost_aware: bool = True
    max_cost_per_1k_tokens: float = 10.0


class PromptCacheConfig(BaseModel):
    """Configuration for prompt caching."""
    enabled: bool = True
    cache_ttl_seconds: int = 3600
    max_cache_size_mb: int = 100
    cache_key_prefix: str = "prompt_cache"
    cache_providers: List[str] = Field(default_factory=lambda: ["anthropic", "openai"])
    min_tokens_for_caching: int = 1024  # Minimum tokens to bother caching


class StructuredOutputConfig(BaseModel):
    """Configuration for structured output enforcement."""
    enabled: bool = True
    strict_mode: bool = True  # If True, reject responses that don't match schema
    fallback_to_text: bool = False  # If True, return text on schema validation failure
    supported_providers: List[str] = Field(default_factory=lambda: ["openai", "anthropic", "ollama", "vllm"])


class FunctionCallingShimConfig(BaseModel):
    """Configuration for function calling shim."""
    enabled: bool = True
    supported_providers: List[str] = Field(default_factory=lambda: ["openai", "anthropic", "ollama", "vllm", "tgi"])
    convert_to_tools_format: bool = True  # Convert to OpenAI tools format
    parallel_calls: bool = True
    max_parallel_calls: int = 5


class ModelPromptTemplate(BaseModel):
    """Model-specific prompt template."""
    provider_id: str
    model: str
    system_template: str
    user_template: str
    assistant_template: str
    function_calling_template: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)  # Template variables


class ProviderMarketplaceEntry(BaseModel):
    """A provider entry in the marketplace."""
    id: str
    name: str
    description: str
    provider_type: str
    version: str
    author: str
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    downloads: int = 0
    rating: float = 0.0
    verified: bool = False
    created_at: int
    updated_at: int


class BYOKConfig(BaseModel):
    """Bring Your Own Key configuration per agent."""
    agent_id: str
    provider: str
    api_key: Optional[str] = None
    api_key_env: Optional[str] = None
    valid: bool = False
    last_validated: Optional[int] = None
    permissions: List[str] = Field(default_factory=list)  # e.g., ["chat", "embeddings", "functions"]


class ProviderCostBudget(BaseModel):
    """Cost budget per provider."""
    id: str
    provider_id: str
    budget_usd: float
    spent_usd: float = 0.0
    period_start: int
    period_end: int
    alert_threshold_pct: float = 80.0
    hard_stop: bool = False
    per_model_limits: Dict[str, float] = Field(default_factory=dict)  # model -> max cost per 1k tokens


class ProviderMarketplaceConfig(BaseModel):
    """Marketplace configuration."""
    enabled: bool = True
    auto_update: bool = False
    update_interval_hours: int = 24
    allow_unverified: bool = False
    max_entries: int = 100


class LLMRoutingConfig(BaseModel):
    """LLM routing configuration."""
    strategy: Literal["priority", "cost_optimized", "latency_optimized", "quality_optimized", "round_robin"] = "priority"
    prefer_keyless: bool = True
    prefer_local: bool = True
    max_fallback_attempts: int = 3
    fallback_timeout_s: float = 30.0
    cost_weight: float = 0.3
    latency_weight: float = 0.4
    quality_weight: float = 0.3
    health_check_interval_s: int = 60


# --- Phase 10: Memory & Knowledge --------------------------------------------

class VectorMemoryConfigRequest(BaseModel):
    backend: Optional[str] = None  # pgvector, qdrant, weaviate
    pgvector_dsn: Optional[str] = None
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimensions: Optional[int] = None


class EpisodicMemoryConfigRequest(BaseModel):
    max_episodes_per_agent: Optional[int] = None
    auto_summarize: Optional[bool] = None
    min_importance_to_keep: Optional[float] = None


class SemanticMemoryConfigRequest(BaseModel):
    auto_link_concepts: Optional[bool] = None
    max_related_concepts: Optional[int] = None


class ConsolidationConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    interval_hours: Optional[int] = None
    max_items_per_run: Optional[int] = None
    summarization_model: Optional[str] = None
    importance_threshold: Optional[float] = None
    min_access_count: Optional[int] = None
    decay_factor: Optional[float] = None
    create_semantic_concepts: Optional[bool] = None
    create_episodic_summaries: Optional[bool] = None


class KnowledgeGraphConfigRequest(BaseModel):
    max_entities: Optional[int] = None
    max_relations: Optional[int] = None
    enable_vector_search: Optional[bool] = None


class RAGConfigRequest(BaseModel):
    repo_path: Optional[str] = None
    max_commits: Optional[int] = None
    max_diff_size: Optional[int] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    index_branches: Optional[List[str]] = None


class MemoryManagerConfigRequest(BaseModel):
    vector: Optional[VectorMemoryConfigRequest] = None
    episodic: Optional[EpisodicMemoryConfigRequest] = None
    semantic: Optional[SemanticMemoryConfigRequest] = None
    consolidation: Optional[ConsolidationConfigRequest] = None
    knowledge_graph: Optional[KnowledgeGraphConfigRequest] = None
    rag: Optional[RAGConfigRequest] = None
    enable_auto_consolidation: Optional[bool] = None
    consolidation_interval_hours: Optional[int] = None


class MemoryPinRequest(BaseModel):
    agent_id: str
    content: str
    context: Dict[str, Any] = Field(default_factory=dict)
    source: str
    tags: List[str] = Field(default_factory=list)
    importance: float = 1.0
    created_by: Optional[str] = None


class EpisodeRequest(BaseModel):
    agent_id: str
    task_description: str
    context: Dict[str, Any]
    actions: List[Dict[str, Any]]
    outcome: str
    success: bool
    lessons_learned: List[str]
    tags: List[str] = Field(default_factory=list)
    importance: float = 1.0


class ConceptRequest(BaseModel):
    name: str
    type: str  # glossary_term, architecture_decision, design_pattern, api_endpoint, database_schema, configuration, business_rule, technology, custom
    definition: str
    context: str
    examples: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    confidence: float = 1.0
    created_by: Optional[str] = None


class ADRRequest(BaseModel):
    title: str
    status: str  # proposed, accepted, deprecated, superseded
    context: str
    decision: str
    consequences: List[str]
    alternatives: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None


class CodeEntityRequest(BaseModel):
    type: str  # file, function, class, module, api_endpoint, database_table, configuration, dependency, concept, agent, task, custom
    name: str
    qualified_name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None
    confidence: float = 1.0


class CodeRelationRequest(BaseModel):
    source_id: str
    target_id: str
    type: str  # contains, calls, inherits, imports, depends_on, defines, uses, related_to, part_of, has_type, configures
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class MemorySearchRequest(BaseModel):
    query: str
    agent_id: Optional[str] = None
    top_k: int = 10
    include_episodic: bool = True
    include_semantic: bool = True
    include_pins: bool = True
    include_knowledge_graph: bool = True
    include_git_history: bool = False


class MemoryExportRequest(BaseModel):
    agent_id: Optional[str] = None
    include_episodic: bool = True
    include_semantic: bool = True
    include_pins: bool = True
    include_knowledge_graph: bool = False


class MemoryImportRequest(BaseModel):
    pack: Dict[str, Any]
    agent_id: Optional[str] = None


class GitExplainRequest(BaseModel):
    file_path: str
    start_line: int
    end_line: int


class GitQueryRequest(BaseModel):
    question: str
    top_k: int = 10
    include_commits: bool = True
    include_diffs: bool = True
    include_blame: bool = False
    file_path: Optional[str] = None
