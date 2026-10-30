"""Autonomous sales laboratory: lead scoring, outreach, conversion."""
import math


def lead_score(lead):
    score = 0.0
    if lead.get("budget", 0) > 1000:
        score += 0.3
    if lead.get("authority"):
        score += 0.3
    if lead.get("need"):
        score += 0.2
    if lead.get("timeline_days", 999) <= 30:
        score += 0.2
    return round(score, 3)


def outreach_message(lead, template):
    return {"to": lead.get("email"), "subject": template.get("subject", "Hello").format(name=lead.get("name", "")), "body": template.get("body", "").format(name=lead.get("name", ""))}


def conversion_probability(lead, touches):
    base = lead_score(lead)
    boost = min(0.3, touches * 0.05)
    return round(min(1.0, base + boost), 3)


def pipeline_value(leads):
    return round(sum(l.get("deal_value", 0) * conversion_probability(l, l.get("touches", 0)) for l in leads), 2)


def segment_leads(leads):
    hot = [l for l in leads if lead_score(l) >= 0.7]
    warm = [l for l in leads if 0.4 <= lead_score(l) < 0.7]
    cold = [l for l in leads if lead_score(l) < 0.4]
    return {"hot": hot, "warm": warm, "cold": cold}
