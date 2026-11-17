# GH-EXP-001 Participant Study Plan (§7.1)

**Date:** 2026-11-16  
**Study type:** Moderated qualitative + task-based evaluation  
**Participants:** 5 engineers + 5 integrity reviewers (10 total)

## Purpose
Evaluate whether the GH-EXP-001 hero/message variants help target users understand and verify mem20's auditability claim (grounded vs simulated, evidence-gated promotion, provenance/audit trail) and identify comprehension or trust gaps before broader rollout.

## Research questions
1. Can participants correctly explain the grounded vs simulated partition and why it matters?
2. Can participants identify where to verify claims (docs/repo surfaces/proof points) without prompting?
3. Which hero/message framing better supports trust and next-step intent for each role?
4. What objections, ambiguities, or missing proof points block confidence?

## Participant plan

| Cohort | Count | Profile | Recruiting criteria |
|---|---:|---|---|
| Engineers | 5 | Software/platform/infra engineers building or integrating agent systems | Experience with LLM/agent tooling, memory/RAG, or system integration; able to assess implementation claims |
| Integrity reviewers | 5 | Security, compliance, risk, QA/audit, or trust & safety reviewers | Experience evaluating auditability, provenance, controls, or evidence quality |

### Screening / balancing notes
- Mix of prior mem20 familiarity (new, aware, evaluator) if possible.
- Avoid all participants coming from the same company/team.
- Capture role, domain, and baseline familiarity for segmentation (anonymized in reporting).

## Task scenarios (two)

### Scenario A — Engineer integration trust check
**Prompt/context:** You are evaluating mem20 for an agent workflow where incorrect recalled memory could cause harmful actions. Review the presented hero/page content and answer:
- What guarantee (if any) does mem20 make about grounded vs simulated memory?
- How would a dream/simulated record become grounded?
- Where would you look in the product/repo/docs to verify this claim?
- Would you proceed to a technical evaluation? Why/why not?

**Success signals (observed):**
- Correctly distinguishes grounded vs simulated partitions.
- Identifies evidence-gated promotion (not automatic/manual override).
- Names at least one concrete verification surface (e.g. README/docs/code path/tool behavior).

### Scenario B — Integrity reviewer auditability assessment
**Prompt/context:** You are assessing whether mem20's memory claims are auditable enough for a governed environment. Review the presented hero/page content and answer:
- What evidence/provenance is available to support memory claims?
- What controls prevent hypothetical/simulated content from being treated as fact?
- What additional proof/artifacts would you require before approval/pilot?
- What risks or ambiguities remain?

**Success signals (observed):**
- Identifies provenance/auditability mechanisms (ledger, origin/store tags, promotion evidence, etc. as presented).
- Recognizes limits/caveats rather than assuming compliance guarantees.
- Produces concrete review questions/evidence requests.

## Session format (45 minutes each)
1. **Intro & consent (5 min):** purpose, recording/notes policy, "testing materials not participant."
2. **Context + baseline (5 min):** role, familiarity, current evaluation criteria.
3. **Scenario tasks (25 min):** run Scenario A or B based on cohort (optionally brief exposure to the other variant if time permits).
4. **Debrief (10 min):** comprehension check, trust/confidence rating, objections, preferred framing/proof points.

## Materials
- GH-EXP-001 control and treatment hero variants (or screenshots/static captures if live switchback unavailable).
- Scenario prompt sheets and moderator guide.
- Note-taking template with rubric fields (comprehension, verifiability, trust, objections, next-step intent).

## Data capture and synthesis
- Record task outcomes using a simple rubric per scenario: `correct / partial / incorrect / unclear`.
- Tag qualitative findings by theme: claim clarity, proof discoverability, terminology, trust blockers, role-specific needs.
- Separate observed evidence from interpretation; include representative quotes (anonymized).
- Compare responses across cohorts and variants (directional only; small sample).

## Read-out
- **Fast read-out (within 3 days of final session):** top comprehension gaps, top trust blockers, variant preference signals by cohort.
- **Full memo (within 7 days):** findings, severity-ranked issues, recommended copy/proof/UI changes, and open questions for follow-up measurement.

## Ethics and privacy
- Obtain informed consent; allow opt-out at any time.
- Minimize collection of personal data; anonymize notes and quotes in shared artifacts.
- Do not present study results as statistically significant; report as qualitative evidence with sample limits.
