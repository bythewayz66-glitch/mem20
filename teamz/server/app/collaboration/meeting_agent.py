"""Meeting agent: joins calls, transcribes, extracts action items."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class MeetingStatus(str, Enum):
    """Meeting status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    ENDED = "ended"
    CANCELLED = "cancelled"


class ParticipantRole(str, Enum):
    """Participant roles in meeting."""
    HOST = "host"
    CO_HOST = "co_host"
    PARTICIPANT = "participant"
    AGENT = "agent"
    OBSERVER = "observer"


@dataclass
class MeetingParticipant:
    """A participant in a meeting."""
    user_id: str
    name: str
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    joined_at: Optional[float] = None
    left_at: Optional[float] = None
    is_agent: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptSegment:
    """A segment of meeting transcript."""
    id: str
    speaker_id: str
    speaker_name: str
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    is_agent: bool = False
    language: str = "en"


@dataclass
class ActionItem:
    """An action item extracted from meeting."""
    id: str
    description: str
    assignee: Optional[str] = None
    assignee_name: Optional[str] = None
    due_date: Optional[float] = None
    priority: str = "normal"  # low, normal, high, critical
    status: str = "open"  # open, in_progress, done, cancelled
    source_segment_ids: List[str] = field(default_factory=list)
    context: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MeetingSummary:
    """Summary of a meeting."""
    meeting_id: str
    title: str
    key_topics: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    duration_minutes: float = 0.0
    transcript_segments: int = 0
    generated_at: float = field(default_factory=time.time)


@dataclass
class Meeting:
    """A meeting session."""
    id: str
    title: str
    description: str = ""
    host_id: str = ""
    status: MeetingStatus = MeetingStatus.SCHEDULED
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    participants: List[MeetingParticipant] = field(default_factory=list)
    transcript: List[TranscriptSegment] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    summary: Optional[MeetingSummary] = None
    recording_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class MeetingConfig(BaseModel):
    """Configuration for meeting agent."""
    auto_transcribe: bool = True
    auto_extract_actions: bool = True
    auto_generate_summary: bool = True
    transcription_language: str = "en"
    transcription_model: str = "whisper-base"
    action_extraction_model: str = "gpt-4o-mini"
    summary_model: str = "gpt-4o-mini"
    max_transcript_length: int = 10000
    auto_join_enabled: bool = True
    join_before_host: bool = False
    recording_enabled: bool = False
    notification_webhook: Optional[str] = None


class MeetingAgent:
    """Meeting agent that joins calls, transcribes, and extracts action items."""

    def __init__(
        self,
        config: Optional[MeetingConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        transcriber: Optional[Callable[[bytes, str], List[TranscriptSegment]]] = None,
        action_extractor: Optional[Callable[[List[TranscriptSegment], Dict[str, Any]], List[ActionItem]]] = None,
        summarizer: Optional[Callable[[List[TranscriptSegment], Dict[str, Any]], MeetingSummary]] = None,
    ) -> None:
        self.config = config or MeetingConfig()
        self.notifier = notifier
        self.transcriber = transcriber or self._default_transcriber
        self.action_extractor = action_extractor or self._default_action_extractor
        self.summarizer = summarizer or self._default_summarizer
        self._meetings: Dict[str, Meeting] = {}
        self._active_meetings: Dict[str, Meeting] = {}  # meeting_id -> meeting

    def schedule_meeting(
        self,
        title: str,
        host_id: str,
        scheduled_at: float,
        description: str = "",
        participants: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Schedule a new meeting."""
        meeting_id = str(uuid.uuid4())[:8]

        meeting = Meeting(
            id=meeting_id,
            title=title,
            description=description,
            host_id=host_id,
            scheduled_at=scheduled_at,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Add host as participant
        meeting.participants.append(MeetingParticipant(
            user_id=host_id,
            name="Host",
            role=ParticipantRole.HOST,
        ))

        # Add other participants
        for p_id in participants or []:
            meeting.participants.append(MeetingParticipant(
                user_id=p_id,
                name=f"User {p_id}",
                role=ParticipantRole.PARTICIPANT,
            ))

        self._meetings[meeting_id] = meeting
        return meeting_id

    def start_meeting(self, meeting_id: str) -> bool:
        """Start a scheduled meeting."""
        meeting = self._meetings.get(meeting_id)
        if not meeting or meeting.status != MeetingStatus.SCHEDULED:
            return False

        meeting.status = MeetingStatus.IN_PROGRESS
        meeting.started_at = time.time()
        meeting.updated_at = time.time()

        self._active_meetings[meeting_id] = meeting

        # Notify participants
        self._notify_participants(meeting, "meeting_started", {
            "meeting_id": meeting_id,
            "title": meeting.title,
        })

        return True

    def end_meeting(self, meeting_id: str) -> bool:
        """End an active meeting."""
        meeting = self._meetings.get(meeting_id)
        if not meeting or meeting.status != MeetingStatus.IN_PROGRESS:
            return False

        meeting.status = MeetingStatus.ENDED
        meeting.ended_at = time.time()
        meeting.updated_at = time.time()

        # Generate summary if enabled
        if self.config.auto_generate_summary:
            meeting.summary = self.summarizer(meeting.transcript, {
                "title": meeting.title,
                "participants": [p.name for p in meeting.participants],
            })
            meeting.action_items = meeting.summary.action_items

        self._active_meetings.pop(meeting_id, None)

        # Notify participants
        self._notify_participants(meeting, "meeting_ended", {
            "meeting_id": meeting.id,
            "duration_minutes": (meeting.ended_at - meeting.started_at) / 60 if meeting.started_at else 0,
        })

        return True

    def add_participant(
        self,
        meeting_id: str,
        user_id: str,
        name: str,
        role: ParticipantRole = ParticipantRole.PARTICIPANT,
    ) -> bool:
        """Add a participant to a meeting."""
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        participant = MeetingParticipant(
            user_id=user_id,
            name=name,
            role=role,
            joined_at=time.time() if meeting.status == MeetingStatus.IN_PROGRESS else None,
        )
        meeting.participants.append(participant)
        meeting.updated_at = time.time()
        return True

    def remove_participant(self, meeting_id: str, user_id: str) -> bool:
        """Remove a participant from a meeting."""
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        participant = next((p for p in meeting.participants if p.user_id == user_id), None)
        if participant:
            participant.left_at = time.time()
            meeting.updated_at = time.time()
            return True
        return False

    def add_transcript(
        self,
        meeting_id: str,
        speaker_id: str,
        speaker_name: str,
        text: str,
        start_time: float,
        end_time: float,
        confidence: float = 1.0,
        is_agent: bool = False,
    ) -> Optional[str]:
        """Add a transcript segment."""
        meeting = self._meetings.get(meeting_id)
        if not meeting or meeting.status != MeetingStatus.IN_PROGRESS:
            return None

        segment = TranscriptSegment(
            id=str(uuid.uuid4())[:8],
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            text=text,
            start_time=start_time,
            end_time=end_time,
            confidence=confidence,
            is_agent=is_agent,
        )
        meeting.transcript.append(segment)
        meeting.updated_at = time.time()

        # Extract action items if enabled
        if self.config.auto_extract_actions and len(meeting.transcript) % 10 == 0:
            new_actions = self.action_extractor(meeting.transcript[-10:], {
                "meeting_title": meeting.title,
                "participants": [p.name for p in meeting.participants],
            })
            for action in new_actions:
                meeting.action_items.append(action)

        return segment.id

    def add_action_item(
        self,
        meeting_id: str,
        description: str,
        assignee: Optional[str] = None,
        assignee_name: Optional[str] = None,
        due_date: Optional[float] = None,
        priority: str = "normal",
        context: str = "",
    ) -> Optional[str]:
        """Manually add an action item."""
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return None

        action = ActionItem(
            id=str(uuid.uuid4())[:8],
            description=description,
            assignee=assignee,
            assignee_name=assignee_name,
            due_date=due_date,
            priority=priority,
            context=context,
        )
        meeting.action_items.append(action)
        meeting.updated_at = time.time()
        return action.id

    def update_action_item(
        self,
        meeting_id: str,
        action_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update an action item."""
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        action = next((a for a in meeting.action_items if a.id == action_id), None)
        if not action:
            return False

        for key, value in updates.items():
            if hasattr(action, key):
                setattr(action, key, value)

        action.updated_at = time.time()
        if updates.get("status") == "done":
            action.completed_at = time.time()

        meeting.updated_at = time.time()
        return True

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a meeting by ID."""
        return self._meetings.get(meeting_id)

    def get_active_meetings(self) -> List[Meeting]:
        """Get all active meetings."""
        return list(self._active_meetings.values())

    def get_meetings_for_user(self, user_id: str) -> List[Meeting]:
        """Get meetings a user participated in."""
        return [
            m for m in self._meetings.values()
            if any(p.user_id == user_id for p in m.participants)
        ]

    def get_action_items_for_user(self, user_id: str, status: Optional[str] = None) -> List[ActionItem]:
        """Get action items assigned to a user."""
        items = []
        for meeting in self._meetings.values():
            for action in meeting.action_items:
                if action.assignee == user_id:
                    if not status or action.status == status:
                        items.append(action)
        return items

    def _default_transcriber(
        self,
        audio_data: bytes,
        language: str,
    ) -> List[TranscriptSegment]:
        """Default transcriber (placeholder)."""
        return []

    def _default_action_extractor(
        self,
        transcript_segments: List[TranscriptSegment],
        context: Dict[str, Any],
    ) -> List[ActionItem]:
        """Default action extractor using keyword matching."""
        actions = []
        action_keywords = [
            "action item", "todo", "follow up", "follow-up",
            "will do", "need to", "should", "must",
            "assign", "responsible for", "owner",
        ]

        full_text = " ".join(s.text for s in transcript_segments)

        for keyword in action_keywords:
            if keyword in full_text.lower():
                # Find the sentence containing the keyword
                for segment in transcript_segments:
                    if keyword in segment.text.lower():
                        actions.append(ActionItem(
                            id=str(uuid.uuid4())[:8],
                            description=segment.text[:200],
                            assignee=None,
                            source_segment_ids=[segment.id],
                            context=f"Extracted from: {segment.speaker_name} said '{segment.text[:100]}'",
                        ))
                        break

        return actions[:5]  # Limit to 5 actions per batch

    def _default_summarizer(
        self,
        transcript_segments: List[TranscriptSegment],
        context: Dict[str, Any],
    ) -> MeetingSummary:
        """Default summarizer."""
        full_text = " ".join(s.text for s in transcript_segments)

        # Simple keyword-based topic extraction
        topics = []
        topic_keywords = {
            "architecture": ["architecture", "design", "system", "structure"],
            "deployment": ["deploy", "release", "ci/cd", "pipeline"],
            "testing": ["test", "coverage", "unit test", "integration"],
            "security": ["security", "vulnerability", "auth", "permission"],
            "performance": ["performance", "latency", "optimize", "slow"],
            "bug": ["bug", "issue", "error", "fix", "crash"],
            "feature": ["feature", "implement", "add", "new"],
        }

        for topic, keywords in topic_keywords.items():
            if any(k in full_text.lower() for k in keywords):
                topics.append(topic)

        return MeetingSummary(
            meeting_id="",
            title=context.get("title", "Meeting"),
            key_topics=topics,
            decisions=[],
            action_items=[],
            participants=context.get("participants", []),
            duration_minutes=0,
            transcript_segments=len(transcript_segments),
        )

    def _notify_participants(self, meeting: Meeting, event: str, data: Dict[str, Any]) -> None:
        """Notify all participants of an event."""
        for participant in meeting.participants:
            # In a real implementation, this would use a notification system
            pass


# Global instance
_meeting_agent: Optional[MeetingAgent] = None


def get_meeting_agent(config: Optional[MeetingConfig] = None) -> MeetingAgent:
    """Get global meeting agent instance."""
    global _meeting_agent
    if _meeting_agent is None:
        _meeting_agent = MeetingAgent(config)
    return _meeting_agent