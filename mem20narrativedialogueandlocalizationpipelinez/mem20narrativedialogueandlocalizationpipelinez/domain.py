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

# 1st-class extensions (#339)
def build_narrative_graph(payload=None):
    payload=dict(payload or {})
    text=payload.get("text") or payload.get("script") or "NPC: Hello.\nHERO: Ready."
    parsed=parse_dialogue(text)
    valid=validate_dialogue(parsed if parsed is not None else {"lines":[]})
    locs={}
    for lang in (payload.get("target_languages") or ["en"]):
        locs[lang]=localize(parsed if parsed is not None else {"lines":[]}, lang)
    nodes=[{"id":f"line-{i}","type":"dialogue","data":ln} for i,ln in enumerate((parsed.get("lines") if isinstance(parsed,dict) else parsed) or [])] or [{"id":"line-0","type":"dialogue","data":{"text":text}}]
    edges=[{"from":nodes[i]["id"],"to":nodes[i+1]["id"],"type":"next"} for i in range(len(nodes)-1)]
    return {"ok":bool(valid.get("valid",True)) if isinstance(valid,dict) else True,"parsed":parsed,"validation":valid,"localizations":locs,"graph":{"nodes":nodes,"edges":edges},"word_count":word_count(parsed if isinstance(parsed,list) else [])}

def export_narrative(payload=None):
    g=build_narrative_graph(payload)
    g["export"]=export_script(g["parsed"] if g.get("parsed") is not None else {"lines":[]})
    return g
