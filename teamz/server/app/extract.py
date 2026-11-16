from __future__ import annotations

from typing import Any, Iterable, Optional


def _join_text_parts(parts: Iterable[Any]) -> str:
    out: list[str] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, str):
            if part:
                out.append(part)
            continue
        if isinstance(part, dict):
            # OpenAI-style content parts: {"type":"text","text":"..."}
            # Anthropic-style blocks: {"type":"text","text":"..."} or {"text":"..."}
            ptype = part.get("type")
            if ptype in (None, "text", "output_text"):
                text = part.get("text")
                if isinstance(text, str) and text:
                    out.append(text)
                    continue
                # Some providers nest as {"text":{"value":"..."}}
                if isinstance(text, dict):
                    val = text.get("value")
                    if isinstance(val, str) and val:
                        out.append(val)
                        continue
            # Refusal/other text-bearing shapes
            for key in ("content", "output_text", "value"):
                val = part.get(key)
                if isinstance(val, str) and val:
                    out.append(val)
                    break
            continue
        # Fallback: ignore unknown non-text parts
    return "".join(out)


def extract_text(payload: Any) -> Optional[str]:
    """Extract assistant/user-visible text from common LLM response shapes.

    Supports:
    - plain strings
    - {"reply"/"text"/"message"/"content"/"output": "..."}
    - OpenAI chat: choices[0].message.content (str or list of parts)
    - OpenAI delta/stream chunk: choices[0].delta.content
    - Anthropic-style: content as a list of blocks [{"type":"text","text":"..."}]
      including mixed blocks (non-text blocks are ignored, text blocks preserved)
    - Responses-like: output_text or output[].content[].text
    """
    if payload is None:
        return None
    if isinstance(payload, str):
        s = payload.strip()
        return s if s else None
    if not isinstance(payload, dict):
        return None

    # 1) Simple top-level keys
    for key in ("reply", "text", "message", "output_text"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, list):
            joined = _join_text_parts(val).strip()
            if joined:
                return joined

    # "content" at top-level can be string or Anthropic-style blocks list
    content = payload.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        joined = _join_text_parts(content).strip()
        if joined:
            return joined

    # "output" can be string or responses-style list
    output = payload.get("output")
    if isinstance(output, str) and output.strip():
        return output.strip()
    if isinstance(output, list):
        # Responses API: output[].content[].text or output[].type==message...
        texts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            c = item.get("content")
            if isinstance(c, str) and c:
                texts.append(c)
            elif isinstance(c, list):
                t = _join_text_parts(c)
                if t:
                    texts.append(t)
            elif isinstance(item.get("text"), str):
                texts.append(item["text"])
        joined = "".join(texts).strip()
        if joined:
            return joined

    # 2) OpenAI chat completions
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        choice0 = choices[0] if isinstance(choices[0], dict) else None
        if isinstance(choice0, dict):
            # Non-streaming message
            msg = choice0.get("message")
            if isinstance(msg, dict):
                mc = msg.get("content")
                if isinstance(mc, str) and mc.strip():
                    return mc.strip()
                if isinstance(mc, list):
                    joined = _join_text_parts(mc).strip()
                    if joined:
                        return joined
                # Some providers put reasoning/content variants; try generic text fields
                for k in ("text", "output_text"):
                    v = msg.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
            # Streaming delta
            delta = choice0.get("delta")
            if isinstance(delta, dict):
                dc = delta.get("content")
                if isinstance(dc, str) and dc:
                    return dc  # may be partial chunk; caller decides stripping
                if isinstance(dc, list):
                    joined = _join_text_parts(dc)
                    if joined:
                        return joined
            # Legacy text completion
            t = choice0.get("text")
            if isinstance(t, str) and t.strip():
                return t.strip()

    # 3) Error passthrough text not handled here (caller should inspect errors separately)
    return None


def extract_delta(payload: Any) -> Optional[str]:
    """Extract incremental text from a streaming chunk/delta payload."""
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload if payload else None
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        delta = choices[0].get("delta") or {}
        if isinstance(delta, dict):
            dc = delta.get("content")
            if isinstance(dc, str):
                return dc
            if isinstance(dc, list):
                return _join_text_parts(dc)
        # Some non-standard streams put text directly
        msg = choices[0].get("message") or {}
        if isinstance(msg, dict):
            mc = msg.get("content")
            if isinstance(mc, str):
                return mc
    # Anthropic-like streaming events sometimes carry delta/text
    delta = payload.get("delta")
    if isinstance(delta, dict):
        t = delta.get("text") or delta.get("content")
        if isinstance(t, str):
            return t
    if payload.get("type") == "content_block_delta":
        d = payload.get("delta") or {}
        if isinstance(d, dict) and isinstance(d.get("text"), str):
            return d["text"]
    return None
