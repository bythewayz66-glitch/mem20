"""Narrative dialogue and localization pipeline."""
import re


def parse_dialogue(text):
    lines = []
    for line in text.strip().splitlines():
        if ":" in line:
            speaker, msg = line.split(":", 1)
            lines.append({"speaker": speaker.strip(), "text": msg.strip()})
        else:
            lines.append({"speaker": "narrator", "text": line.strip()})
    return lines


def localize(dialogue, locale, translations=None):
    translations = translations or {}
    out = []
    for d in dialogue:
        key = d["text"]
        tr = translations.get(locale, {}).get(key, key)
        out.append({"speaker": d["speaker"], "text": tr, "locale": locale})
    return out


def validate_dialogue(dialogue):
    issues = []
    for d in dialogue:
        if not d.get("text"):
            issues.append({"issue": "empty text", "speaker": d.get("speaker")})
    return {"valid": not issues, "issues": issues}


def word_count(dialogue):
    return sum(len(d.get("text", "").split()) for d in dialogue)


def export_script(dialogue, format="txt"):
    return "\n".join(f'{d["speaker"]}: {d["text"]}' for d in dialogue)
