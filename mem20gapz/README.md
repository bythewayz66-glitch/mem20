# mem20gapz — Capability Gap Mapper

**RM-145** | Section: Capability Intelligence | Owner: Gap (GAP)

## Overview

Maps current vs required capabilities across human skills, agent competencies, tool coverage, infrastructure, data assets, APIs, process knowledge, and domain expertise. Identifies gaps and recommends bridging strategies with ROI ranking.

## Breakthrough

Unified capability taxonomy spanning human skills, agent competencies, tool coverage, and infrastructure — enabling automated gap detection and ROI-ranked remediation.

## Quick Start

```bash
pip install -e .
mem20gapz run '{"current_capabilities": [...], "required_capabilities": [...]}'
```

## API

### Endpoints (via `mem20core.Runtime`)

| RID | Operation | Description |
|-----|-----------|-------------|
| 201 | `gap_detection` | Compute gaps between current and required capabilities |
| 202 | `bridging_strategies` | Generate ranked bridging actions for gaps |
| 203 | `gap_clustering` | Cluster gaps by systemic themes |
| 204 | `acquisition_simulation` | Monte Carlo simulation of capability acquisition |
| 205 | `drift_detection` | Detect capability decay/improvement between snapshots |
| 206 | `full_pipeline` | End-to-end: gaps → clusters → strategies → simulation |

### Request Format

```json
{
  "current_capabilities": [
    {
      "id": "cap-001",
      "name": "Python",
      "category": "human_skill",
      "proficiency": "advanced",
      "tags": ["backend", "data-science"]
    }
  ],
  "required_capabilities": [
    {
      "id": "req-001",
      "capability_id": "cap-001",
      "name": "Rust",
      "category": "human_skill",
      "required_proficiency": "intermediate",
      "criticality": 0.8,
      "urgency": 0.6,
      "rationale": "Performance-critical services migration",
      "tags": ["backend", "performance"]
    }
  ],
  "context": {
    "budget_per_gap": 50000,
    "max_time_days": 180,
    "org_size": 100,
    "strategic_priorities": ["performance", "backend"]
  }
}
```

### Response Format (RID 206 - Full Pipeline)

```json
{
  "gaps": [...],
  "clusters": [...],
  "actions": [...],
  "simulation": {...},
  "summary": {
    "total_gaps": 5,
    "critical_gaps": 2,
    "total_clusters": 3,
    "systemic_clusters": 1,
    "total_actions": 12,
    "top_action": {...},
    "expected_gaps_closed": 3.2,
    "expected_cost": 145000.0
  }
}
```

## Capability Categories

| Category | Description | Typical Strategies |
|----------|-------------|-------------------|
| `human_skill` | Human technical/soft skills | TRAIN, HIRE, REDEPLOY |
| `agent_competency` | AI agent capabilities | BUILD, BUY, AUTOMATE |
| `tool_coverage` | Tool/platform coverage | BUY, BUILD |
| `infrastructure` | Infra/platform capabilities | BUILD, BUY, PARTNER |
| `data_asset` | Data availability/quality | BUILD, BUY, PARTNER |
| `api_integration` | API/integration coverage | BUILD, BUY, PARTNER |
| `process_knowledge` | Process/operational knowledge | TRAIN, BUILD |
| `domain_expertise` | Business domain knowledge | HIRE, TRAIN, PARTNER |

## Bridging Strategies

| Strategy | Description | Typical Cost | Typical Time |
|----------|-------------|--------------|--------------|
| `hire` | Recruit external talent | $80k | 90 days |
| `train` | Upskill existing team | $5k | 30 days |
| `build` | Internal development | $150k | 120 days |
| `buy` | Commercial procurement | $50k | 30 days |
| `partner` | Strategic partnership | $30k | 60 days |
| `automate` | Agent/tool automation | $100k | 90 days |
| `redeploy` | Internal reassignment | $2k | 14 days |
| `defer` | Delay investment | $0 | 0 days |

## Proficiency Levels

`none` (0.0) → `aware` (0.15) → `basic` (0.35) → `intermediate` (0.6) → `advanced` (0.8) → `expert` (1.0)

## CLI Usage

```bash
# Run gap detection (RID 201)
mem20gapz run '{"current_capabilities": [...], "required_capabilities": [...]}'

# Run full pipeline (RID 206)
mem20gapz run '{"current_capabilities": [...], "required_capabilities": [...], "context": {...}}' --rid 206

# Start HTTP server
mem20gapz serve --port 8768

# Run simulator
mem20gapz simulate

# Run benchmark
mem20gapz benchmark --runs 10
```

## Architecture

```
mem20gapz/
├── mem20gapz/
│   ├── __init__.py          # Public exports
│   └── core.py              # Domain algorithms + family_capability_gap_mapper
├── tests/
│   └── test_core.py         # Comprehensive test suite
├── roadmap.json             # RM-145 roadmap definition
├── run.py                   # CLI entry point
├── pyproject.toml           # Package metadata
├── SAMPLE_REQUEST.json      # Example request
└── ROLLBACK.json            # Rollback metadata
```

## Integration

Registers with `mem20core.Runtime` via `FAMILY_FUNCS["Gap"] = family_capability_gap_mapper`.

The Runtime loads `roadmap.json` (global_id=145) and routes requests to the family function.

## Testing

```bash
pytest tests/ -v
```

## License

MIT