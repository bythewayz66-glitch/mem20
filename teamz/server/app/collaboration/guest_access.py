"""Guest access: read-only links for PMs, designers, execs."""

from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class GuestRole(str, Enum):
    """Guest roles with different permissions."""
    VIEWER = "viewer"              # Read-only access
    COMMENTER = "commenter"        # Can add comments
    REVIEWER = "reviewer"          # Can review and approve
    STAKEHOLDER = "stakeholder"    # High-level view only


class GuestStatus(str, Enum):
    """Guest access status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class ResourceType(str, Enum):
    """Types of resources guests can access."""
    PROJECT = "project"
    ROOM = "room"
    DOCUMENT = "document"
    DASHBOARD = "dashboard"
    REPORT = "report"
    WHITEBOARD = "whiteboard"
    CODE_REVIEW = "code_review"
    METRICS = "metrics"
    CUSTOM = "custom"


@dataclass
class GuestToken:
    """A guest access token."""
    id: str
    token: str  # The actual shareable token
    role: GuestRole
    resource_type: ResourceType
    resource_id: str
    resource_name: str
    created_by: str
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    max_uses: Optional[int] = None
    uses_count: int = 0
    status: GuestStatus = GuestStatus.ACTIVE
    allowed_ips: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_accessed_at: Optional[float] = None
    revoked_at: Optional[float] = None
    revoked_by: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if token is valid for use."""
        if self.status != GuestStatus.ACTIVE:
            return False

        if self.expires_at and time.time() > self.expires_at:
            return False

        if self.max_uses and self.uses_count >= self.max_uses:
            return False

        return True

    def use(self, client_ip: Optional[str] = None) -> bool:
        """Record a use of the token."""
        if not self.is_valid():
            return False

        self.uses_count += 1
        self.last_accessed_at = time.time()

        # Check IP restrictions
        if client_ip and self.allowed_ips:
            if client_ip not in self.allowed_ips:
                return False

        return True


@dataclass
class GuestSession:
    """An active guest session."""
    id: str
    token_id: str
    guest_ip: str
    user_agent: str
    started_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GuestConfig(BaseModel):
    """Configuration for guest access."""
    default_expiry_hours: float = 168.0  # 1 week
    max_expiry_hours: float = 720.0  # 30 days
    default_max_uses: Optional[int] = None
    require_authentication: bool = False
    allow_ip_restriction: bool = True
    allow_domain_restriction: bool = True
    session_timeout_minutes: float = 60.0
    max_concurrent_sessions: int = 5
    audit_log_enabled: bool = True
    notification_webhook: Optional[str] = None


class GuestAccessManager:
    """Manages guest access tokens and sessions."""

    def __init__(
        self,
        config: Optional[GuestConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        resource_resolver: Optional[Callable[[ResourceType, str], Optional[Dict[str, Any]]]] = None,
    ) -> None:
        self.config = config or GuestConfig()
        self.notifier = notifier
        self.resource_resolver = resource_resolver
        self._tokens: Dict[str, GuestToken] = {}  # token_id -> token
        self._token_lookup: Dict[str, str] = {}  # token string -> token_id
        self._sessions: Dict[str, GuestSession] = {}  # session_id -> session
        self._user_tokens: Dict[str, Set[str]] = {}  # user_id -> token_ids

    def create_token(
        self,
        role: GuestRole,
        resource_type: ResourceType,
        resource_id: str,
        created_by: str,
        expires_in_hours: Optional[float] = None,
        max_uses: Optional[int] = None,
        resource_name: Optional[str] = None,
        allowed_ips: Optional[List[str]] = None,
        allowed_domains: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GuestToken:
        """Create a new guest access token."""
        token_id = str(uuid.uuid4())[:12]
        token_string = self._generate_token()

        # Resolve resource name if not provided
        if resource_name is None and self.resource_resolver:
            resource = self.resource_resolver(resource_type, resource_id)
            if resource:
                resource_name = resource.get("name", resource_id)

        expires_at = None
        if expires_in_hours:
            expires_at = time.time() + min(expires_in_hours, self.config.max_expiry_hours) * 3600
        else:
            expires_at = time.time() + self.config.default_expiry_hours * 3600

        token = GuestToken(
            id=token_id,
            token=token_string,
            role=role,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name or resource_id,
            created_by=created_by,
            expires_at=expires_at,
            max_uses=max_uses,
            allowed_ips=allowed_ips or [],
            allowed_domains=allowed_domains or [],
            metadata=metadata or {},
        )

        self._tokens[token_id] = token
        self._token_lookup[token_string] = token_id
        self._user_tokens.setdefault(created_by, set()).add(token_id)

        # Notify creator
        self._notify(created_by, "guest_token_created", {
            "token_id": token_id,
            "resource_name": token.resource_name,
            "role": role.value,
            "expires_at": expires_at,
            "share_url": self._get_share_url(token_string),
        })

        return token

    def _generate_token(self) -> str:
        """Generate a secure random token."""
        return f"guest_{secrets.token_urlsafe(32)}"

    def _get_share_url(self, token: str) -> str:
        """Generate a shareable URL for the token."""
        base_url = "https://teamz.example.com/guest"  # Would be configured
        return f"{base_url}?token={token}"

    def get_token(self, token_id: str) -> Optional[GuestToken]:
        """Get a token by ID."""
        return self._tokens.get(token_id)

    def get_token_by_string(self, token_string: str) -> Optional[GuestToken]:
        """Get a token by its string value."""
        token_id = self._token_lookup.get(token_string)
        if token_id:
            return self._tokens.get(token_id)
        return None

    def validate_token(
        self,
        token_string: str,
        client_ip: Optional[str] = None,
    ) -> Optional[GuestToken]:
        """Validate and use a token."""
        token = self.get_token_by_string(token_string)
        if not token or not token.is_valid():
            return None

        if not token.use(client_ip):
            return None

        return token

    def create_session(
        self,
        token_string: str,
        client_ip: str,
        user_agent: str,
    ) -> Optional[GuestSession]:
        """Create a guest session from a valid token."""
        token = self.validate_token(token_string, client_ip)
        if not token:
            return None

        # Check concurrent sessions
        active_sessions = sum(
            1 for s in self._sessions.values()
            if s.token_id == token.id and time.time() - s.last_activity < self.config.session_timeout_minutes * 60
        )

        if active_sessions >= self.config.max_concurrent_sessions:
            return None

        session = GuestSession(
            id=str(uuid.uuid4())[:8],
            token_id=token.id,
            guest_ip=client_ip,
            user_agent=user_agent,
        )

        self._sessions[session.id] = session
        return session

    def end_session(self, session_id: str) -> bool:
        """End a guest session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def revoke_token(self, token_id: str, revoked_by: str) -> bool:
        """Revoke a guest token."""
        token = self._tokens.get(token_id)
        if not token:
            return False

        token.status = GuestStatus.REVOKED
        token.revoked_at = time.time()
        token.revoked_by = revoked_by

        # End any active sessions
        for session in list(self._sessions.values()):
            if session.token_id == token_id:
                del self._sessions[session.id]

        # Notify creator
        self._notify(token.created_by, "guest_token_revoked", {
            "token_id": token_id,
            "resource_name": token.resource_name,
            "revoked_by": revoked_by,
        })

        return True

    def extend_token(self, token_id: str, additional_hours: float, extended_by: str) -> bool:
        """Extend a token's expiry."""
        token = self._tokens.get(token_id)
        if not token:
            return False

        if token.status != GuestStatus.ACTIVE:
            return False

        new_expiry = time.time() + min(additional_hours, self.config.max_expiry_hours) * 3600
        if token.expires_at and new_expiry <= token.expires_at:
            return False  # Not an extension

        token.expires_at = new_expiry

        # Notify creator
        self._notify(token.created_by, "guest_token_extended", {
            "token_id": token_id,
            "new_expiry": new_expiry,
        })

        return True

    def get_user_tokens(self, user_id: str) -> List[GuestToken]:
        """Get all tokens created by a user."""
        token_ids = self._user_tokens.get(user_id, set())
        return [self._tokens[tid] for tid in token_ids if tid in self._tokens]

    def get_resource_tokens(
        self,
        resource_type: ResourceType,
        resource_id: str,
    ) -> List[GuestToken]:
        """Get all tokens for a resource."""
        return [
            t for t in self._tokens.values()
            if t.resource_type == resource_type and t.resource_id == resource_id
        ]

    def cleanup_expired(self) -> int:
        """Clean up expired tokens and sessions."""
        expired_count = 0

        # Expire tokens
        for token in list(self._tokens.values()):
            if token.status == GuestStatus.ACTIVE and token.expires_at and time.time() > token.expires_at:
                token.status = GuestStatus.EXPIRED
                expired_count += 1

        # Clean up stale sessions
        cutoff = time.time() - self.config.session_timeout_minutes * 60
        for session_id, session in list(self._sessions.items()):
            if session.last_activity < cutoff:
                del self._sessions[session_id]

        return expired_count

    def get_access_log(self, token_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get access log for a token (placeholder - would need actual logging)."""
        token = self._tokens.get(token_id)
        if not token:
            return []

        return [{
            "uses_count": token.uses_count,
            "last_accessed": token.last_accessed_at,
            "created_at": token.created_at,
            "status": token.status.value,
        }]

    def _notify(self, user_id: str, event: str, data: Dict[str, Any]) -> None:
        """Notify a user of an event."""
        if not self.notifier:
            return

        try:
            self.notifier(user_id, event, data)
        except Exception:
            pass


# Global instance
_guest_access_manager: Optional[GuestAccessManager] = None


def get_guest_access(config: Optional[GuestConfig] = None) -> GuestAccessManager:
    """Get global guest access manager instance."""
    global _guest_access_manager
    if _guest_access_manager is None:
        _guest_access_manager = GuestAccessManager(config)
    return _guest_access_manager