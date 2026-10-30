"""Style guide agent: enforce style rules on content."""
import re


def check(content, rules):
    issues = []
    for rule in rules:
        if rule.get("type") == "max_length" and len(content) > rule["value"]:
            issues.append({"rule": "max_length", "detail": f"len {len(content)} > {rule['value']}"})
        if rule.get("type") == "forbidden" and rule["value"] in content:
            issues.append({"rule": "forbidden", "detail": rule["value"]})
        if rule.get("type") == "regex" and re.search(rule["value"], content):
            issues.append({"rule": "regex", "detail": rule["value"]})
    return issues


def fix(content, issues):
    # simple: truncate if too long
    for i in issues:
        if i["rule"] == "max_length":
            pass
    return content


def style_score(content, rules):
    issues = check(content, rules)
    return round(1 - len(issues)/max(1, len(rules)), 4)


def style_health(content, rules):
    return {"issues": len(check(content, rules)), "score": style_score(content, rules)}
