"""Code review UI: inline comments, suggestions, approve/request changes."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ReviewDecision(str, Enum):
    """Code review decision."""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"


class CommentType(str, Enum):
    """Types of review comments."""
    INLINE = "inline"        # On specific line
    GENERAL = "general"      # General feedback
    SUGGESTION = "suggestion"  # Code suggestion
    QUESTION = "question"    # Clarification question
    PRAISE = "praise"        # Positive feedback


class ReviewStatus(str, Enum):
    """Status of a code review."""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"
    CLOSED = "closed"


@dataclass
class ReviewComment:
    """A comment on a code review."""
    id: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    type: CommentType = CommentType.INLINE
    author: str = ""
    content: str = ""
    suggestion: Optional[str] = None  # For suggestion type
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[float] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> [user_ids]
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    thread_id: Optional[str] = None  # For threaded replies
    parent_id: Optional[str] = None
    replies: List["ReviewComment"] = field(default_factory=list)


@dataclass
class CodeReview:
    """A code review."""
    id: str
    title: str
    description: str
    author: str
    reviewers: List[str] = field(default_factory=list)
    status: ReviewStatus = ReviewStatus.DRAFT
    base_branch: str = "main"
    head_branch: str = ""
    files_changed: List[str] = field(default_factory=list)
    diff: str = ""  # Unified diff
    comments: List[ReviewComment] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)  # {reviewer, decision, timestamp}
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    submitted_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_comment(self, comment: ReviewComment) -> None:
        self.comments.append(comment)
        self.updated_at = time.time()

    def get_comments_for_file(self, file_path: str) -> List[ReviewComment]:
        return [c for c in self.comments if c.file_path == file_path]

    def get_inline_comments(self, file_path: str, line: int) -> List[ReviewComment]:
        return [
            c for c in self.comments
            if c.file_path == file_path
            and c.line_start is not None
            and c.line_start <= line <= (c.line_end or c.line_start)
        ]

    def get_unresolved_comments(self) -> List[ReviewComment]:
        return [c for c in self.comments if not c.resolved]

    def add_decision(self, reviewer: str, decision: ReviewDecision, rationale: str = "") -> None:
        self.decisions.append({
            "reviewer": reviewer,
            "decision": decision.value,
            "rationale": rationale,
            "timestamp": time.time(),
        })
        self.updated_at = time.time()

        # Update status based on decisions
        approve_count = sum(1 for d in self.decisions if d["decision"] == ReviewDecision.APPROVE.value)
        changes_count = sum(1 for d in self.decisions if d["decision"] == ReviewDecision.REQUEST_CHANGES.value)

        if changes_count > 0:
            self.status = ReviewStatus.CHANGES_REQUESTED
        elif approve_count > 0 and changes_count == 0:
            self.status = ReviewStatus.APPROVED

    def is_approved(self) -> bool:
        return self.status == ReviewStatus.APPROVED

    def needs_changes(self) -> bool:
        return self.status == ReviewStatus.CHANGES_REQUESTED


class ReviewConfig(BaseModel):
    """Configuration for code review."""
    required_approvals: int = 1
    require_all_reviewers: bool = False
    auto_assign_reviewers: bool = True
    reviewer_pools: Dict[str, List[str]] = Field(default_factory=dict)  # path_pattern -> [reviewers]
    require_ci_pass: bool = True
    allow_suggestions: bool = True
    suggestion_apply_threshold: int = 3  # Max suggestions to auto-apply
    comment_threading: bool = True
    draft_by_default: bool = True


class CodeReviewManager:
    """Manages code reviews."""

    def __init__(
        self,
        config: Optional[ReviewConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        ci_checker: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self.config = config or ReviewConfig()
        self.notifier = notifier
        self.ci_checker = ci_checker
        self._reviews: Dict[str, CodeReview] = {}
        self._user_reviews: Dict[str, Set[str]] = {}  # user_id -> review_ids

    def create_review(
        self,
        title: str,
        description: str,
        author: str,
        head_branch: str,
        base_branch: str = "main",
        files_changed: Optional[List[str]] = None,
        diff: str = "",
        reviewers: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new code review."""
        review_id = str(uuid.uuid4())[:8]

        review = CodeReview(
            id=review_id,
            title=title,
            description=description,
            author=author,
            reviewers=reviewers or [],
            base_branch=base_branch,
            head_branch=head_branch,
            files_changed=files_changed or [],
            diff=diff,
            status=ReviewStatus.DRAFT if self.config.draft_by_default else ReviewStatus.PENDING,
            metadata=metadata or {},
        )

        self._reviews[review_id] = review

        for reviewer in review.reviewers:
            self._user_reviews.setdefault(reviewer, set()).add(review_id)
        self._user_reviews.setdefault(author, set()).add(review_id)

        if review.status == ReviewStatus.PENDING:
            self._notify_reviewers(review)

        return review_id

    def submit_review(self, review_id: str) -> bool:
        """Submit a draft review for review."""
        review = self._reviews.get(review_id)
        if not review or review.status != ReviewStatus.DRAFT:
            return False

        review.status = ReviewStatus.PENDING
        review.submitted_at = time.time()
        review.updated_at = time.time()

        self._notify_reviewers(review)
        return True

    def add_comment(
        self,
        review_id: str,
        author: str,
        file_path: str,
        content: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        comment_type: CommentType = CommentType.INLINE,
        suggestion: Optional[str] = None,
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Optional[str]:
        """Add a comment to a review."""
        review = self._reviews.get(review_id)
        if not review:
            return None

        comment = ReviewComment(
            id=str(uuid.uuid4())[:8],
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            type=comment_type,
            author=author,
            content=content,
            suggestion=suggestion,
            thread_id=thread_id,
            parent_id=parent_id,
        )

        # Handle threaded replies
        if parent_id:
            parent = next((c for c in review.comments if c.id == parent_id), None)
            if parent:
                parent.replies.append(comment)
                comment.thread_id = parent.thread_id or parent_id
        elif thread_id:
            comment.thread_id = thread_id

        review.add_comment(comment)
        self._notify_comment(review, comment)

        return comment.id

    def resolve_comment(self, review_id: str, comment_id: str, resolver: str) -> bool:
        """Mark a comment as resolved."""
        review = self._reviews.get(review_id)
        if not review:
            return False

        comment = next((c for c in review.comments if c.id == comment_id), None)
        if not comment:
            return False

        comment.resolved = True
        comment.resolved_by = resolver
        comment.resolved_at = time.time()
        review.updated_at = time.time()

        return True

    def add_reaction(self, review_id: str, comment_id: str, user_id: str, emoji: str) -> bool:
        """Add a reaction to a comment."""
        review = self._reviews.get(review_id)
        if not review:
            return False

        comment = next((c for c in review.comments if c.id == comment_id), None)
        if not comment:
            return False

        if emoji not in comment.reactions:
            comment.reactions[emoji] = []
        if user_id not in comment.reactions[emoji]:
            comment.reactions[emoji].append(user_id)
            return True
        return False

    def submit_decision(
        self,
        review_id: str,
        reviewer: str,
        decision: ReviewDecision,
        rationale: str = "",
    ) -> bool:
        """Submit a review decision."""
        review = self._reviews.get(review_id)
        if not review:
            return False

        if reviewer not in review.reviewers and reviewer != review.author:
            return False

        review.add_decision(reviewer, decision, rationale)

        # Check if review is complete
        if review.is_approved() and self._all_required_approved(review):
            review.status = ReviewStatus.APPROVED
            review.completed_at = time.time()
            self._notify_completion(review)
        elif review.needs_changes():
            review.status = ReviewStatus.CHANGES_REQUESTED
            self._notify_changes_requested(review)

        return True

    def _all_required_approved(self, review: CodeReview) -> bool:
        """Check if all required reviewers have approved."""
        if self.config.require_all_reviewers:
            required = set(review.reviewers)
            approved = {d["reviewer"] for d in review.decisions if d["decision"] == ReviewDecision.APPROVE.value}
            return required.issubset(approved)

        # Check minimum approvals
        approve_count = sum(1 for d in review.decisions if d["decision"] == ReviewDecision.APPROVE.value)
        return approve_count >= self.config.required_approvals

    def get_review(self, review_id: str) -> Optional[CodeReview]:
        """Get a review by ID."""
        return self._reviews.get(review_id)

    def get_reviews_for_user(self, user_id: str, status: Optional[ReviewStatus] = None) -> List[CodeReview]:
        """Get reviews for a user."""
        review_ids = self._user_reviews.get(user_id, set())
        reviews = [self._reviews[rid] for rid in review_ids if rid in self._reviews]
        if status:
            reviews = [r for r in reviews if r.status == status]
        return reviews

    def get_pending_reviews(self, user_id: str) -> List[CodeReview]:
        """Get reviews pending user's action."""
        return self.get_reviews_for_user(user_id, ReviewStatus.PENDING)

    def _notify_reviewers(self, review: CodeReview) -> None:
        """Notify reviewers of new review."""
        if not self.notifier:
            return

        for reviewer in review.reviewers:
            try:
                self.notifier(
                    reviewer,
                    "review_assigned",
                    {
                        "review_id": review.id,
                        "title": review.title,
                        "author": review.author,
                        "files_changed": review.files_changed,
                    },
                )
            except Exception:
                pass

    def _notify_comment(self, review: CodeReview, comment: ReviewComment) -> None:
        """Notify relevant users of new comment."""
        if not self.notifier:
            return

        # Notify author and thread participants
        participants = {review.author}
        for c in review.comments:
            if c.thread_id == comment.thread_id:
                participants.add(c.author)

        for user in participants:
            if user != comment.author:
                try:
                    self.notifier(
                        user,
                        "review_comment",
                        {
                            "review_id": review.id,
                            "comment_id": comment.id,
                            "file_path": comment.file_path,
                            "line": comment.line_start,
                            "author": comment.author,
                            "preview": comment.content[:100],
                        },
                    )
                except Exception:
                    pass

    def _notify_completion(self, review: CodeReview) -> None:
        """Notify review completion."""
        if not self.notifier:
            return

        try:
            self.notifier(
                review.author,
                "review_approved",
                {
                    "review_id": review.id,
                    "title": review.title,
                },
            )
        except Exception:
            pass

    def _notify_changes_requested(self, review: CodeReview) -> None:
        """Notify changes requested."""
        if not self.notifier:
            return

        try:
            self.notifier(
                review.author,
                "review_changes_requested",
                {
                    "review_id": review.id,
                    "title": review.title,
                },
            )
        except Exception:
            pass


# Global instance
_code_review_manager: Optional[CodeReviewManager] = None


def get_code_review(config: Optional[ReviewConfig] = None) -> CodeReviewManager:
    """Get global code review manager instance."""
    global _code_review_manager
    if _code_review_manager is None:
        _code_review_manager = CodeReviewManager(config)
    return _code_review_manager