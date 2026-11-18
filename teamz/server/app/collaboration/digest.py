"""Stakeholder digest: daily/weekly summary email/Slack."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class DigestFrequency(str, Enum):
    """Digest frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


class DigestFormat(str, Enum):
    """Digest output format."""
    EMAIL = "email"
    SLACK = "slack"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class ContentType(str, Enum):
    """Types of content in digest."""
    ACTIVITY = "activity"
    METRICS = "metrics"
    ALERTS = "alerts"
    MILESTONES = "milestones"
    ACTION_ITEMS = "action_items"
    DECISIONS = "decisions"
    RISKS = "risks"
    UPCOMING = "upcoming"
    CUSTOM = "custom"


@dataclass
class DigestSection:
    """A section in a digest."""
    type: ContentType
    title: str
    content: List[Dict[str, Any]]
    order: int = 0
    visible: bool = True


@dataclass
class DigestTemplate:
    """Template for digest generation."""
    id: str
    name: str
    description: str
    sections: List[DigestSection] = field(default_factory=list)
    format: DigestFormat = DigestFormat.MARKDOWN
    frequency: DigestFrequency = DigestFrequency.DAILY
    recipients: List[str] = field(default_factory=list)  # User IDs or emails
    filters: Dict[str, Any] = field(default_factory=dict)  # Project, team, etc.
    schedule: Dict[str, Any] = field(default_factory=dict)  # Cron-like schedule
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class Digest:
    """A generated digest."""
    id: str
    template_id: str
    title: str
    sections: List[DigestSection] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)
    period_start: float = 0.0
    period_end: float = 0.0
    recipients: List[str] = field(default_factory=list)
    format: DigestFormat = DigestFormat.MARKDOWN
    status: str = "generated"  # generated, sent, failed
    sent_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DigestConfig(BaseModel):
    """Configuration for digest generator."""
    default_frequency: DigestFrequency = DigestFrequency.DAILY
    default_format: DigestFormat = DigestFormat.MARKDOWN
    max_items_per_section: int = 10
    include_empty_sections: bool = False
    timezone: str = "UTC"
    delivery_webhook: Optional[str] = None
    email_sender: Optional[str] = None
    slack_webhook: Optional[str] = None


class DigestGenerator:
    """Generates stakeholder digests from activity data."""

    def __init__(
        self,
        config: Optional[DigestConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        data_providers: Optional[Dict[ContentType, Callable[[Dict[str, Any], float, float], List[Dict[str, Any]]]]] = None,
    ) -> None:
        self.config = config or DigestConfig()
        self.notifier = notifier
        self.data_providers = data_providers or {}
        self._templates: Dict[str, DigestTemplate] = {}
        self._generated_digests: Dict[str, Digest] = {}

    def create_template(self, template: DigestTemplate) -> str:
        """Create a digest template."""
        template.id = template.id or str(uuid.uuid4())[:8]
        template.created_at = time.time()
        template.updated_at = time.time()
        self._templates[template.id] = template
        return template.id

    def get_template(self, template_id: str) -> Optional[DigestTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def list_templates(self) -> List[DigestTemplate]:
        """List all templates."""
        return list(self._templates.values())

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update a template."""
        template = self._templates.get(template_id)
        if not template:
            return False

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = time.time()
        return True

    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def generate_digest(
        self,
        template_id: str,
        period_start: Optional[float] = None,
        period_end: Optional[float] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Optional[Digest]:
        """Generate a digest from a template."""
        template = self._templates.get(template_id)
        if not template:
            return None

        # Calculate period
        now = time.time()
        if period_end is None:
            period_end = now
        if period_start is None:
            # Default to 24 hours for daily, 7 days for weekly
            if template.frequency == DigestFrequency.DAILY:
                period_start = period_end - 86400
            elif template.frequency == DigestFrequency.WEEKLY:
                period_start = period_end - 604800
            elif template.frequency == DigestFrequency.MONTHLY:
                period_start = period_end - 2592000
            else:
                period_start = period_end - 86400

        # Apply overrides
        filters = {**template.filters, **(overrides.get("filters", {}) if overrides else {})}

        # Generate sections
        sections = []
        for section_template in template.sections:
            if not section_template.visible:
                continue

            content = self._fetch_section_content(
                section_template.type,
                filters,
                period_start,
                period_end,
            )

            if content or self.config.include_empty_sections:
                sections.append(DigestSection(
                    type=section_template.type,
                    title=section_template.title,
                    content=content[:self.config.max_items_per_section],
                    order=section_template.order,
                    visible=True,
                ))

        # Sort sections by order
        sections.sort(key=lambda s: s.order)

        # Create digest
        digest = Digest(
            id=str(uuid.uuid4())[:8],
            template_id=template_id,
            title=f"{template.name} - {time.strftime('%Y-%m-%d', time.localtime(period_end))}",
            sections=sections,
            period_start=period_start,
            period_end=period_end,
            recipients=template.recipients,
            format=template.format,
        )

        self._generated_digests[digest.id] = digest
        return digest

    def _fetch_section_content(
        self,
        content_type: ContentType,
        filters: Dict[str, Any],
        period_start: float,
        period_end: float,
    ) -> List[Dict[str, Any]]:
        """Fetch content for a section type."""
        provider = self.data_providers.get(content_type)
        if provider:
            return provider(filters, period_start, period_end)

        # Default empty content
        return []

    def register_data_provider(
        self,
        content_type: ContentType,
        provider: Callable[[Dict[str, Any], float, float], List[Dict[str, Any]]],
    ) -> None:
        """Register a data provider for a content type."""
        self.data_providers[content_type] = provider

    def format_digest(self, digest: Digest, format: Optional[DigestFormat] = None) -> str:
        """Format a digest for output."""
        output_format = format or digest.format

        if output_format == DigestFormat.MARKDOWN:
            return self._format_markdown(digest)
        elif output_format == DigestFormat.HTML:
            return self._format_html(digest)
        elif output_format == DigestFormat.JSON:
            return self._format_json(digest)
        elif output_format == DigestFormat.SLACK:
            return self._format_slack(digest)
        else:
            return self._format_markdown(digest)

    def _format_markdown(self, digest: Digest) -> str:
        """Format digest as Markdown."""
        lines = [
            f"# {digest.title}",
            f"**Period:** {time.strftime('%Y-%m-%d %H:%M', time.localtime(digest.period_start))} to {time.strftime('%Y-%m-%d %H:%M', time.localtime(digest.period_end))}",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(digest.generated_at))}",
            "",
        ]

        for section in digest.sections:
            if not section.content:
                continue

            lines.append(f"## {section.title}")
            lines.append("")

            for item in section.content:
                lines.append(self._format_item_markdown(item))

            lines.append("")

        return "\n".join(lines)

    def _format_item_markdown(self, item: Dict[str, Any]) -> str:
        """Format a single item as Markdown."""
        if "title" in item:
            title = item["title"]
            desc = item.get("description", "")
            url = item.get("url", "")
            meta = item.get("meta", "")

            line = f"- **{title}**"
            if desc:
                line += f": {desc}"
            if meta:
                line += f" ({meta})"
            if url:
                line += f" [[link]({url})]"
            return line

        return f"- {item}"

    def _format_html(self, digest: Digest) -> str:
        """Format digest as HTML."""
        html = [
            "<html><body>",
            f"<h1>{digest.title}</h1>",
            f"<p>Period: {time.strftime('%Y-%m-%d', time.localtime(digest.period_start))} to {time.strftime('%Y-%m-%d', time.localtime(digest.period_end))}</p>",
            f"<p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(digest.generated_at))}</p>",
        ]

        for section in digest.sections:
            if not section.content:
                continue

            html.append(f"<h2>{section.title}</h2>")
            html.append("<ul>")

            for item in section.content:
                html.append(f"<li>{self._format_item_html(item)}</li>")

            html.append("</ul>")

        html.append("</body></html>")
        return "\n".join(html)

    def _format_item_html(self, item: Dict[str, Any]) -> str:
        """Format a single item as HTML."""
        if "title" in item:
            parts = [f"<strong>{item['title']}</strong>"]
            if item.get("description"):
                parts.append(f"<span>{item['description']}</span>")
            if item.get("meta"):
                parts.append(f"<em>{item['meta']}</em>")
            if item.get("url"):
                parts.append(f'<a href="{item["url"]}">link</a>')
            return " ".join(parts)

        return str(item)

    def _format_json(self, digest: Digest) -> str:
        """Format digest as JSON."""
        return json.dumps({
            "id": digest.id,
            "title": digest.title,
            "template_id": digest.template_id,
            "period_start": digest.period_start,
            "period_end": digest.period_end,
            "generated_at": digest.generated_at,
            "format": digest.format.value,
            "sections": [
                {
                    "type": s.type.value,
                    "title": s.title,
                    "content": s.content,
                }
                for s in digest.sections
            ],
        }, indent=2)

    def _format_slack(self, digest: Digest) -> str:
        """Format digest for Slack (Block Kit JSON)."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": digest.title,
                    "emoji": True,
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Period: {time.strftime('%Y-%m-%d', time.localtime(digest.period_start))} - {time.strftime('%Y-%m-%d', time.localtime(digest.period_end))}",
                    },
                ],
            },
            {"type": "divider"},
        ]

        for section in digest.sections:
            if not section.content:
                continue

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{section.title}*",
                },
            })

            for item in section.content:
                if "title" in item:
                    text = f"*{item['title']}*"
                    if item.get("description"):
                        text += f"\n{item['description']}"
                    if item.get("meta"):
                        text += f"\n_{item['meta']}_"
                    if item.get("url"):
                        text += f"\n<{item['url']}|View Details>"

                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": text,
                        },
                    })

            blocks.append({"type": "divider"})

        return json.dumps({"blocks": blocks}, indent=2)

    def send_digest(self, digest: Digest) -> bool:
        """Send a digest to recipients."""
        if not self.notifier:
            return False

        formatted = self.format_digest(digest)

        for recipient in digest.recipients:
            try:
                self.notifier(recipient, "digest", {
                    "digest_id": digest.id,
                    "title": digest.title,
                    "format": digest.format.value,
                    "content": formatted,
                })
            except Exception:
                return False

        digest.status = "sent"
        digest.sent_at = time.time()
        return True

    def get_digest(self, digest_id: str) -> Optional[Digest]:
        """Get a generated digest."""
        return self._generated_digests.get(digest_id)

    def list_digests(
        self,
        template_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Digest]:
        """List generated digests."""
        digests = list(self._generated_digests.values())

        if template_id:
            digests = [d for d in digests if d.template_id == template_id]

        digests.sort(key=lambda d: d.generated_at, reverse=True)
        return digests[:limit]


# Global instance
_digest_generator: Optional[DigestGenerator] = None


def get_digest_generator(config: Optional[DigestConfig] = None) -> DigestGenerator:
    """Get global digest generator instance."""
    global _digest_generator
    if _digest_generator is None:
        _digest_generator = DigestGenerator(config)
    return _digest_generator