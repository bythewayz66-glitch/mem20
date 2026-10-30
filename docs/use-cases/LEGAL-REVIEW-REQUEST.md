# Legal / Regulatory Review Request — mem20liez

**Date:** 2026-10-30  
**Component:** mem20liez (live behavioural signal detection)  
**Modes of concern:** clinical, government, interrogation  
**Status:** Review **not yet obtained** — do not treat this document as legal advice or as completed clearance.

## Why this request exists

mem20liez produces probabilistic voice-stress, micro-motion, and linguistic indicators and can seal an immutable package into grounded memory. It is explicitly **not** a polygraph or medical device, but its government and clinical modes sit near regulated activity. A formal external review is required before production deployment in those modes.

## Questions for counsel / compliance

1. **Classification**  
   Does any current or planned use cause mem20liez to be treated as a medical device, polygraph, or similar regulated instrument in the target jurisdiction(s)?

2. **Consent**  
   Is the current consent gate (`consent=true` + `consent_attested_by`, re-checked at seal) sufficient for clinical and government interview settings? What additional notice or form is required?

3. **Biometric / sensitive data**  
   Do voice-stress features and facial micro-motion scores constitute biometric or special-category data under applicable privacy law (e.g. GDPR Art. 9, state biometric laws, HIPAA if PHI is in scope)?

4. **Evidentiary use**  
   Under what conditions, if any, may a sealed package be introduced in administrative or judicial proceedings? What disclaimer language is mandatory?

5. **Prohibited uses**  
   Confirm or extend the prohibited-use list in `mem20liez/mem20liez/gates.py` (automated detention/charge/clearance, definitive deception claims, clinical diagnosis, polygraph substitute, covert use without authority, employment screening without notice, immigration/child-custody sole basis).

6. **Retention & subject rights**  
   What retention, access, correction, and deletion duties apply to sealed packages that contain indicator data?

7. **Cross-border**  
   Any transfer restrictions when jurisdiction metadata indicates a foreign authority?

## Artefacts supplied for review

| Artefact | Path |
|----------|------|
| System description | `mem20liez/README.md` |
| Consent / dual-control / prohibited-use gates | `mem20liez/mem20liez/gates.py` |
| Session + seal path | `mem20liez/mem20liez/session.py` |
| MCP tool surface | `mem20liez/mem20liez/mcp_tools.py` |
| Government use case | `docs/use-cases/UC-MEM-AV-GOV-001.md` |
| General AV use case | `docs/use-cases/UC-MEM-AV-001.md` |
| Risk register | `docs/use-cases/RISK-REGISTER-LIEZ.md` |
| Operator training | `docs/use-cases/TRAINING-MEM20LIEZ.md` |
| Voice-stress engine (classical features) | `mem20liez/mem20liez/detectors/voice_stress.py` |
| Manipulation rules (linguistic) | `mem20liez/mem20liez/detectors/manipulation.py` |

## Interim controls (until review completes)

- Production clinical / government deployments are **not authorised** by this repository alone.
- Training acknowledgement and consent gates remain enforced in code.
- Dual-control is mandatory for government high-priority cues.
- Contamination firewall rejects definitive-claim annotations at seal.

## Requested deliverable from counsel

A short written opinion covering classification, consent sufficiency, evidentiary limits, and any required changes to prohibited uses or retention. Attach the opinion (or a redacted summary) under `docs/use-cases/` when available and update the risk register residual ratings.
