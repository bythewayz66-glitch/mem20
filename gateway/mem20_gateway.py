#!/usr/bin/env python3
"""
mem20 Gateway — CLI relay for multi-agent fleet communication.
Each mem20 agent picks a unique name on startup to avoid confusion.
Stage 1: CLI procede. No fake code. Real tools only.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

MEM20_DIR = Path("/opt/mem20")
GATEWAY_DIR = MEM20_DIR / "gateway"
NAMES_FILE = GATEWAY_DIR / "agent_names.json"
MESSAGES_FILE = GATEWAY_DIR / "messages.jsonl"

# ---------------------------------------------------------------------------
# Subsystem registry
# ---------------------------------------------------------------------------
# Which mem20 subsystems are reachable from the gateway surface, and what each
# one is for. A subsystem that is not listed here is not callable by any client,
# which is the state 204 of the 211 subsystems were in at the 4.0 baseline.
#
# This is a registry, not a wish list: an entry means the subsystem has a CLI
# surface the gateway can shell out to, and the ``entry`` field names it. Adding
# a row without a working entry point would make the gateway claim a capability
# it cannot deliver, so the conformance gate checks the name is present and the
# subsystem's own tests check the entry point runs.
SUBSYSTEMS = {
    "mem20intentcompilerz": {
        "purpose": "Intent Compiler (RM-051, #329): translate goals into typed executable graphs with resources/constraints/success conditions; 6 peer integrations; legacy domain preserved",
        "entry": "python -m mem20intentcompilerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20integrationdigitaltwinz": {
        "purpose": "Integration Digital Twin (RM-076, #328): simulate external services/rate limits/failures/API changes with 6 peer integrations; legacy domain preserved",
        "entry": "python -m mem20integrationdigitaltwinz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20instantappsynthesisz": {
        "purpose": "Instant App Synthesis (RM-010, #327): compile objectives into capability compositions with 6 peer integrations; legacy domain preserved (#318)",
        "entry": "python -m mem20instantappsynthesisz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20humancapabilitysuperplatformz": {
        "purpose": "Human Capability Super-Platform (RM-220, #326): capability search/assessment/growth with 6 peer integrations; legacy domain preserved (#319)",
        "entry": "python -m mem20humancapabilitysuperplatformz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20humanagentcoworkcanvasz": {
        "purpose": "Human-Agent Co-work Canvas (RM-032, #325): sync humans/agents on tasks, files, decisions, live artifacts with 6 peer integrations; legacy domain preserved (#320)",
        "entry": "python -m mem20humanagentcoworkcanvasz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20hotswappableservicefoundationz": {
        "purpose": "Hot-Swappable Service Foundation (RM-091, #324): zero-disruption service swaps with 6 peer integrations; legacy domain preserved (#317)",
        "entry": "python -m mem20hotswappableservicefoundationz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20hardwaremarketplacez": {
        "purpose": "Hardware Marketplace (RM-048, #323): match workloads to volunteered/owned/rented compute under explicit limits with 6 peer integrations; legacy domain preserved",
        "entry": "python -m mem20hardwaremarketplacez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20hardwareawareinferencecompilerz": {
        "purpose": "Hardware-Aware Inference Compiler (RM-065, #322): fusion/quant/schedule/memory compile with 6 peer integrations; legacy domain preserved (#314)",
        "entry": "python -m mem20hardwareawareinferencecompilerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },

    "mem20shopz": {
        "purpose": "Storefront: catalog, Stripe Checkout, verified webhooks, once-only provisioning",
        "entry": "python -m mem20shopz --readiness",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20sitemapz": {
        "purpose": "Machine-readable sitemap of the estate, quiescence poller, source snapshotter",
        "entry": "python -m mem20sitemapz build",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20kanbanz": {
        "purpose": "The one true kanban door: typed client, migration, read-only inspection",
        "entry": "python -m mem20kanbanz health",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20teamz": {
        "purpose": "Rooms where humans and agents share a transcript; @mentions wake profiles",
        "entry": "python -m mem20teamz rooms",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20officez": {
        "purpose": "Native 3D office, agent fleet, Phaser scenes, wellness, dashboard",
        "entry": "python -m mem20officez doctor",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20famz": {
        "purpose": "Family registry: which family each mem20*z package belongs to, and why",
        "entry": "python -m mem20famz stats",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20boxz": {
        "purpose": "Sandbox runtime grouping the sandbox family for joint integration",
        "entry": "python -m mem20boxz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20biz": {
        "purpose": "Autonomous company and revenue runtime grouping the revenue family",
        "entry": "python -m mem20biz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20multiworldsandboxz": {
        "purpose": "Multi-world sandbox: parallel worlds, branching, merging",
        "entry": "python -m mem20multiworldsandboxz",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20edgetocloudintelligencecontinuumz": {
        "purpose": "Edge-to-cloud continuum: invisible, resilient, cost-aware workload placement across local/edge/private/peer/cloud",
        "entry": "python -m mem20edgetocloudintelligencecontinuumz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
        "mem20graphz": {
        "purpose": "mem20graphz graph crew runtime (#321): 7-member graph integrations (capability-gap, loyalty, config, skill, relationship, reversible execution, semantic objects); legacy CLI preserved",
        "entry": "python -m mem20graphz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20goapagentdesignerz": {
        "purpose": "GOAP Agent Designer (RM-226, #320): goal-oriented planning/design with incentives, quality, collaboration, phasing, ecosystem, capsule integrations; legacy domain preserved",
        "entry": "python -m mem20goapagentdesignerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20multibrandswarmz": {
        "purpose": 'Multi-Brand Swarm (RM-016,#337): multi-brand portfolio with distinct audiences/products, shared infra; 6 peers',
        "entry": 'python -m mem20multibrandswarmz execute \'{"brands":["alpha","beta"]}\'',
        "owner": "mem20-webdev", "wave": 2,
    },
    "mem20multimodaltaskcapturez": {
        "purpose": 'Multimodal Task Capture (RM-037,#338): speech/sketch/screenshot/notes to structured executable work; 6 peers',
        "entry": 'python -m mem20multimodaltaskcapturez execute \'{"text":"build api. test api"}\'',
        "owner": "mem20-webdev", "wave": 2,
    },
    "mem20pipez": {
        "purpose": 'Narrative/Dialogue/Localization Pipeline (RM-244,#339): dialogue graphs, localization, export; 6 peers',
        "entry": 'python -m mem20pipez execute \'{"text":"NPC: Hello\\nHERO: Ready","target_languages":["en","es"]}\'',
        "owner": "mem20-webdev", "wave": 2,
    },
    "mem20modelsleepandwakesystemz": {
        "purpose": "Model Sleep/Wake (RM-066,#336): predictive hibernation/restore; forecast+6 peer integrations",
        "entry": "python -m mem20modelsleepandwakesystemz execute '{\"models\":[{\"id\":\"m1\",\"state\":\"awake\",\"last_activity\":0}],\"idle_threshold\":1}'",
        "owner": "mem20-webdev", "wave": 2,
    },
    "mem20modelgenomelabz": {
        "purpose": "Model Genome Lab (RM-061,#335): model genomes/capabilities/traits/limits/adapters/ancestry; evolution+6 peer integrations",
        "entry": "python -m mem20modelgenomelabz execute '{\"population\":4,\"generations\":2,\"objective\":{\"quality\":1.0}}'",
        "owner": "mem20-webdev", "wave": 2,
    },
    "mem20modalitybridgez": {
        "purpose": "Modality Bridge (RM-064,#334): translate representations across text/image/audio/video/3D/sensor with adapters; 6 peer integrations",
        "entry": "python -m mem20modalitybridgez execute '{\"from\":\"text\",\"to\":\"image\",\"payload\":\"a cat\"}'",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20meshz": {
        "purpose": "Mesh Gold Runtime (#333): orchestrates 6 vendored meshes (crisis/crossdevice/federated/nearby/offline/selfhealing) with 6 external ecosystem integrations, lazy aggregation/failover",
        "entry": "python -m mem20meshz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20pipez": {
        "purpose": "Level/World/Nav Pipeline (RM-246,#332): blockout→nav→streaming→lighting→playability with stages/artifacts/deps/checkpoints; 6 peer integrations",
        "entry": "python -m mem20pipez execute '{\"goal\":\"build level\",\"stages\":[\"blockout\",\"navigation\",\"playability_tests\"],\"grid\":[[0,0],[0,0]],\"rooms\":[{\"id\":\"r1\"}]}'",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20labz": {
        "purpose": "Laboratory Runtime (#331): 1st-class control plane for 10 member labs with registry/probes/simulation, 6-peer ecosystem signals, durable SQLite WAL run history, CLI/API/web",
        "entry": "python -m mem20labz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20intenttomissioncompilerz": {
        "purpose": "Intent-to-Mission Compiler (RM-031, #330): convert objectives into executable missions with dependencies, roles, completion criteria; 6-peer integrations (intent, goal scheduling, priority, skill graph, reversible execution, self-healing planning)",
        "entry": "python -m mem20intenttomissioncompilerz execute '{\"goal\":\"design and ship feature\",\"parts\":[\"design\",\"build\",\"test\"]}'",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20goaleconomyschedulerz": {
        "purpose": "Goal Economy Scheduler (RM-056, #319): goal allocation with plan, opportunity, leak, milestone, capacity, interface integrations; legacy domain preserved",
        "entry": "python -m mem20goaleconomyschedulerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20globalcapabilitymarketplacez": {
        "purpose": "Global Capability Marketplace (RM-218, #318): listings/match/transactions with offer, trial, secure-capsule, query, remix integrations; legacy domain preserved",
        "entry": "python -m mem20globalcapabilitymarketplacez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20gameproductioncontrolcenterz": {
        "purpose": "Game Production Control Center (RM-233, #317): sprints/milestones/risk/health composed with team,cost,release,forge,resilience,asset integrations; legacy domain preserved",
        "entry": "python -m mem20gameproductioncontrolcenterz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20pipez": {
        "purpose": "Gameplay Systems Data & Balance Pipeline (RM-245, #316): telemetry/analysis/tuning pipeline with 6 peer signals; legacy domain preserved",
        "entry": "python -m mem20pipez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20simz": {
        "purpose": "Game Balance Simulator (RM-231, #315): combat/progression/economy simulation with 6 peer signals; legacy domain preserved (#307)",
        "entry": "python -m mem20simz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20freestackambientcomputingfabricz": {
        "purpose": "FreeStack Ambient Computing Fabric (RM-211, #314): ambient pooling/discovery/allocation with 6 peer fabric/inference/capability/microkernel/identity/companion signals",
        "entry": "python -m mem20freestackambientcomputingfabricz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20federatedresearchgridz": {
        "purpose": "Federated Research Grid (RM-043, #313): distributed node search/aggregation with 6 peer intelligence/search/CRDT/priority/connector signals",
        "entry": "python -m mem20federatedresearchgridz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20facez": {
        "purpose": "Interface/Workspace crew runtime (#312): 8-member composition with 6-peer capture, dataflow, mission, canvas, sandbox, and blackboard signals",
        "entry": "python -m mem20facez doctor",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20fabricz": {
        "purpose": "Integration Fabric crew runtime (#311): 23-member registry/probing/dispatch with 6-peer API/integration/episode/event/radio/deal signals",
        "entry": "python -m mem20fabricz doctor",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20executiondigitaltwinz": {
        "purpose": "Execution Digital Twin (RM-059): predictive workflow twin forecast with sync/simulate/drift and peer time-machine/counterfactual/event signals",
        "entry": "python -m mem20executiondigitaltwinz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20pipez": {
        "purpose": "Executable Game Concept & Scope Pipeline (RM-237): concept scoring, scope/feasibility/risk/stage with 6 production/growth/foundry peer signals",
        "entry": "python -m mem20pipez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20executabledesignstresslabz": {
        "purpose": "Executable Design Stress Lab (RM-221): simulated design/production/technical stress tests with resilience, adversarial QA, and experiment peer signals",
        "entry": "python -m mem20executabledesignstresslabz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20simz": {
        "purpose": "Ethical Incentive Simulator (RM-203): incentive/fairness simulation with harm-manipulation safeguards and outcome/risk peer signals",
        "entry": "python -m mem20simz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20episodicmemorygraphz": {
        "purpose": "Episodic Memory Graph (RM-021): linked experiences/people/places/goals/actions/outcomes/time, recall and graph queries, durable state",
        "entry": "python -m mem20episodicmemorygraphz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20enginez": {
        "purpose": "Crew runtime for 30 engine members: registry/probing, compatibility and dispatch planning, durable state, CLI/HTTP cockpit",
        "entry": "python -m mem20enginez status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20energyawarefoundationz": {
        "purpose": "Energy-aware foundation: power monitoring, thresholds, budgets, optimization actions with durable state",
        "entry": "python -m mem20energyawarefoundationz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20energyawarecomputemigrationz": {
        "purpose": "Energy-aware compute migration: battery/thermal/price/renewable-aware placement and migration planning with durable state",
        "entry": "python -m mem20energyawarecomputemigrationz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20edgetransportfabricz": {
        "purpose": "Edge transport fabric: bounded data/command routing, QoS, bandwidth admission/reservation, and resilient reroute across intermittently connected nodes",
        "entry": "python -m mem20edgetransportfabricz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20planetarybatchfabricz": {"purpose": "Planetary Batch Fabric with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20planetarybatchfabricz status","owner":"mem20-renovation","wave":4},
    "mem20pipez": {"purpose": "mem20pipez crew runtime with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20pipez status","owner":"mem20-renovation","wave":4},
    "mem20personalworkflowtwinz": {"purpose": "Personal Workflow Twin with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20personalworkflowtwinz status","owner":"mem20-renovation","wave":4},
    "mem20personalmodelevolutionz": {"purpose": "Personal Model Evolution with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20personalmodelevolutionz status","owner":"mem20-renovation","wave":4},
    "mem20personalcognitivesearchz": {"purpose": "Personal Cognitive Search with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20personalcognitivesearchz status","owner":"mem20-renovation","wave":4},
    "mem20personalautomationcanvasz": {"purpose": "Personal Automation Canvas with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20personalautomationcanvasz status","owner":"mem20-renovation","wave":4},
    "mem20simz": {"purpose": "Outcome Simulation Lab with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20simz status","owner":"mem20-renovation","wave":4},
    "mem20opportunityradarz": {"purpose": "Opportunity Radar with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20opportunityradarz status","owner":"mem20-renovation","wave":4},
    "mem20offergenomeenginez": {"purpose": "Offer Genome Engine with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20offergenomeenginez status","owner":"mem20-renovation","wave":4},
    "mem20offerassemblyfabricz": {"purpose": "Offer Assembly Fabric with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20offerassemblyfabricz status","owner":"mem20-renovation","wave":4},
    "mem20zerotouchnodeswarmz": {
        "purpose": "Zero-touch node swarm: discovery, joining, task distribution, healing",
        "entry": "python -m mem20zerotouchnodeswarmz simulate",
        "owner": "hsp2",
        "wave": 2,
    },
    "mem20pipez": {
        "purpose": "Audio/voice/music pipeline (mix, normalize, sync, export, mastering) with 6 subsystem-specific peer integrations, HTTP cockpit, and MCP tools",
        "entry": "python -m mem20pipez status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20autonomousdealdeskz": {
        "purpose": "Autonomous deal desk (pricing, terms, approval, negotiation) with 6 subsystem-specific peers, HTTP cockpit, MCP tools",
        "entry": "python -m mem20autonomousdealdeskz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20autonomousmicrosaasfoundryz": {
        "purpose": "Autonomous micro-SaaS foundry (idea/MVP/launch/revenue) with 6 subsystem-specific peers, HTTP cockpit, MCP tools",
        "entry": "python -m mem20autonomousmicrosaasfoundryz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20autonomousrecoverydirectorz": {
        "purpose": "Autonomous recovery director (triage/rollback/remediation) with 6 recovery-specific peers, HTTP cockpit, MCP",
        "entry": "python -m mem20autonomousrecoverydirectorz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20autonomoussaleslaboratoryz": {
        "purpose": "Autonomous sales laboratory (leads/outreach/conversion experiments, anti-spam) with 6 sales-lab peers, HTTP cockpit, MCP",
        "entry": "python -m mem20autonomoussaleslaboratoryz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20realtimeeventautopilotz": {"purpose": "Real-Time Event Autopilot with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20realtimeeventautopilotz status","owner":"mem20-renovation","wave":4},
    "mem20realtimebusinesstwinz": {"purpose": "Real-Time Business Twin with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20realtimebusinesstwinz status","owner":"mem20-renovation","wave":4},
    "mem20realitytosoftwarecompilerz": {"purpose": "Reality-to-Software Compiler with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20realitytosoftwarecompilerz status","owner":"mem20-renovation","wave":4},
    "mem20protocolautodiscoveryenginez": {"purpose": "Protocol Auto-Discovery Engine with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20protocolautodiscoveryenginez status","owner":"mem20-renovation","wave":4},
    "mem20simz": {"purpose": "Product-Led Growth Simulator with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20simz status","owner":"mem20-renovation","wave":4},
    "mem20pipez": {"purpose": "Production Planning and Task Orchestration Pipeline with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20pipez status","owner":"mem20-renovation","wave":4},
    "mem20predictiverecallenginez": {"purpose": "Predictive Recall Engine with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20predictiverecallenginez status","owner":"mem20-renovation","wave":4},
    "mem20playermotivationtwinz": {"purpose": "Player Motivation Twin with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20playermotivationtwinz status","owner":"mem20-renovation","wave":4},
    "mem20dynamicskillgraphz": {"purpose": "Dynamic Skill Graph with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20dynamicskillgraphz status","owner":"mem20-renovation","wave":3},
    "mem20dynamicquestrewardcomposerz": {"purpose": "Dynamic Quest Reward Composer with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20dynamicquestrewardcomposerz status","owner":"mem20-renovation","wave":3},
    "mem20dynamicnarrativeenginez": {"purpose": "Dynamic Narrative Engine with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20dynamicnarrativeenginez status","owner":"mem20-renovation","wave":3},
    "mem20devicecapabilitycompilerz": {"purpose": "Device Capability Compiler with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20devicecapabilitycompilerz status","owner":"mem20-renovation","wave":3},
    "mem20deterministicconfigurationgraphz": {"purpose": "Deterministic Configuration Graph with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20deterministicconfigurationgraphz status","owner":"mem20-renovation","wave":3},
    "mem20datalocalityoptimizerz": {"purpose": "Data Locality Optimizer with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20datalocalityoptimizerz status","owner":"mem20-renovation","wave":3},
    "mem20customerlifecycleenginez": {"purpose": "Customer Lifecycle Engine with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20customerlifecycleenginez status","owner":"mem20-renovation","wave":3},
    "mem20customerdigitaltwinlabz": {"purpose": "Customer Digital Twin Lab with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20customerdigitaltwinlabz status","owner":"mem20-renovation","wave":3},
    "mem20crossproductloyaltygraphz": {"purpose": "Cross-Product Loyalty Graph with 6 peers, HTTP cockpit, MCP","entry":"python -m mem20crossproductloyaltygraphz status","owner":"mem20-renovation","wave":3},
    "mem20crossplatformmicrokernelz": {
        "purpose": "Cross-Platform Microkernel with 6 peers, HTTP cockpit, MCP",
        "entry": "python -m mem20crossplatformmicrokernelz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20simz": {
        "purpose": "Counterfactual Memory Simulator with 6 peers, HTTP cockpit, MCP",
        "entry": "python -m mem20simz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20compoundingproductecosystemz": {
        "purpose": "Compounding Product Ecosystem with 6 peers, HTTP cockpit, MCP",
        "entry": "python -m mem20compoundingproductecosystemz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20communitychallengeenginez": {
        "purpose": "Community challenge engine (challenges/leaderboards/rewards) with 6 peers, HTTP cockpit, MCP",
        "entry": "python -m mem20communitychallengeenginez status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20collectivemodelintelligencez": {
        "purpose": "Collective model intelligence (ensemble/voting/diversity) with 6 peers, HTTP cockpit, MCP",
        "entry": "python -m mem20collectivemodelintelligencez status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20causalroutingbrainz": {
        "purpose": "Causal routing brain with 6 causal-routing peers, HTTP cockpit, MCP",
        "entry": "python -m mem20causalroutingbrainz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20simz": {
        "purpose": "Business model simulator (revenue/cost/margin/scenarios) with 6 estate peers, HTTP cockpit, MCP",
        "entry": "python -m mem20simz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20autonomousworkcellsz": {
        "purpose": "Autonomous work cells (queues/workers/throughput) with 6 workcell-specific peers, HTTP cockpit, MCP",
        "entry": "python -m mem20autonomousworkcellsz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20autonomoussoftwarefoundryz": {
        "purpose": "Autonomous software foundry (spec→build→deploy) with 6 software-foundry peers, HTTP cockpit, MCP",
        "entry": "python -m mem20autonomoussoftwarefoundryz status",
        "owner": "mem20-renovation",
        "wave": 3,
    },
    "mem20edgefleetbrainz": {
        "purpose": "Coordinate heterogeneous computers, phones, servers and appliances as one capability-aware fleet",
        "entry": "python -m mem20edgefleetbrainz status",
        "owner": "hsp2",
        "wave": 2,
    },
    "mem20visualdataflowcomposerz": {
        "purpose": "Visual dataflow composer: typed streams wired into debuggable pipelines",
        "entry": "python -m mem20visualdataflowcomposerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20visualagentblackboardz": {
        "purpose": "Expose agent perceptions, goals, memory, plans, messages, and live actions",
        "entry": "python -m mem20visualagentblackboardz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20universalintegrationcompilerz": {
        "purpose": "Compile API descriptions, examples, and observed traffic into working typed connectors",
        "entry": "python -m mem20universalintegrationcompilerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20universalhealthnervoussystemz": {
        "purpose": "Aggregate deep health, dependency, saturation, and recovery signals in real time",
        "entry": "python -m mem20universalhealthnervoussystemz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20uniteconomicsautopilotz": {
        "purpose": "Track contribution margins and recommend operational changes continuously",
        "entry": "python -m mem20uniteconomicsautopilotz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20syntheticevaluatorarenaz": {
        "purpose": "Generate adversarial tasks and continuously compare model behavior under real constraints",
        "entry": "python -m mem20syntheticevaluatorarenaz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20styleguideagentz": {
        "purpose": "Enforce visual, audio, interaction, and narrative style across generated assets in real time",
        "entry": "python -m mem20styleguideagentz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20twinz": {
        "purpose": "mem20 digital twin runtime.",
        "entry": "python -m mem20twinz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20studioz": {
        "purpose": "mem20 studio runtime.",
        "entry": "python -m mem20studioz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20speculativeworkflowenginez": {
        "purpose": "Run low-cost branches ahead of time and commit the best valid path",
        "entry": "python -m mem20speculativeworkflowenginez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20specialistmodelforgez": {
        "purpose": "Create small task-specific models and adapters from successful workflows",
        "entry": "python -m mem20specialistmodelforgez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20spatialcommanduniversez": {
        "purpose": "Represent projects, runtimes, agents, data, and live operations as interactive spatial environments",
        "entry": "python -m mem20spatialcommanduniversez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20skillmemorytransferz": {
        "purpose": "Extract reusable procedures from successful work and apply them to new tasks",
        "entry": "python -m mem20skillmemorytransferz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20skillbasedprogressionbrainz": {
        "purpose": "Advance users according to demonstrated capability rather than time spent",
        "entry": "python -m mem20skillbasedprogressionbrainz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20simz": {
        "purpose": "mem20 simulator runtime.",
        "entry": "python -m mem20simz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20servicebundlingenginez": {
        "purpose": "Discover complementary capabilities and package them into higher-value services",
        "entry": "python -m mem20servicebundlingenginez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20sensorymemoryingestz": {
        "purpose": "Turn images, audio, screens, files, and device signals into searchable episodes",
        "entry": "python -m mem20sensorymemoryingestz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20selfz": {
        "purpose": "mem20 self-healing, self-tuning, forecasting and optimization runtime.",
        "entry": "python -m mem20selfz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20selftuningresourcegovernorz": {
        "purpose": "Continuously adjust CPU, memory, I/O, and queue budgets by observed value and demand",
        "entry": "python -m mem20selftuningresourcegovernorz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20selfoptimizingkernelz": {
        "purpose": "Continuously tune workload placement, caches, queues, and process limits from observed demand",
        "entry": "python -m mem20selfoptimizingkernelz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20selfhealingplansz": {
        "purpose": "Detect plan drift and rebuild only the damaged portion of an execution graph",
        "entry": "python -m mem20selfhealingplansz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20securecomputecapsulesz": {
        "purpose": "Execute risky or untrusted tasks in disposable capability-scoped sandboxes",
        "entry": "python -m mem20securecomputecapsulesz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20secretslessworkloadidentityz": {
        "purpose": "Use short-lived cryptographic workload identities instead of long-lived application secrets",
        "entry": "python -m mem20secretslessworkloadidentityz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20runtimepromptoptimizerz": {
        "purpose": "Continuously compress, test, mutate, and route instructions according to measured task performance",
        "entry": "python -m mem20runtimepromptoptimizerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20runtimecompatibilityenginez": {
        "purpose": "Predict whether modules, schemas, and interfaces can operate together before installation",
        "entry": "python -m mem20runtimecompatibilityenginez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20roamingworkloadschedulerz": {
        "purpose": "Move active jobs between devices as connectivity, cost, and performance change",
        "entry": "python -m mem20roamingworkloadschedulerz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20pipez": {
        "purpose": "Automate skeleton mapping, retargeting, clip validation, IK, compression, and state integration",
        "entry": "python -m mem20pipez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20rewardforgez": {
        "purpose": "Compose digital rewards from value, rarity, timing, eligibility, and delivery rules",
        "entry": "python -m mem20rewardforgez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20revenueleakhunterz": {
        "purpose": "Detect churn risks, failed handoffs, underbilling, unused entitlements, and broken conversion paths",
        "entry": "python -m mem20revenueleakhunterz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20resourceexchangemarketz": {
        "purpose": "Match internal and external demand with available people, agents, compute, and inventory",
        "entry": "python -m mem20resourceexchangemarketz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20remoteexperimentlabz": {
        "purpose": "Run reproducible experiments across device classes and collect live metrics",
        "entry": "python -m mem20remoteexperimentlabz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20realworldimpactrewardsz": {
        "purpose": "Connect verified beneficial actions to digital progression and community recognition",
        "entry": "python -m mem20realworldimpactrewardsz simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20realtimeteampresencez": {
        "purpose": "Show who or what is active, blocked, waiting, learning, or overloaded",
        "entry": "python -m mem20realtimeteampresencez simulate",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20AIonbordz": {"purpose": "Generate verified onboarding packs for mem20 agents (hire guide, orientation)","entry":"python -m mem20aionbordz --help","owner":"mem20-renovation","wave":4},
    "mem20adaptz": {"purpose": "Adaptive systems runtime (crew/runtime)","entry":"python -m mem20adaptz --help","owner":"mem20-renovation","wave":4},
    "mem20agentz_sdk": {"purpose": "Native mem20 OpenAI Agents SDK absorption (Agent, Runner, Tools, Handoffs)","entry":"python -m mem20agentz_sdk --help","owner":"mem20-renovation","wave":4},
    "mem20autouez": {"purpose": "Unreal Engine automation, Python API, asset pipeline absorption","entry":"python -m mem20autouez --help","owner":"mem20-renovation","wave":4},
    "mem20autoz": {"purpose": "Autonomous systems runtime (crew/runtime)","entry":"python -m mem20autoz --help","owner":"mem20-renovation","wave":4},
    "mem20benchmarkz": {"purpose": "Retrieval benchmarks (quality, latency, trustworthiness)","entry":"python -m mem20benchmarkz --help","owner":"mem20-renovation","wave":4},
    "mem20controlz": {"purpose": "Unified control plane for the mem20 fleet (per-subsystem panels)","entry":"python -m mem20controlz --help","owner":"mem20-renovation","wave":4},
    "mem20cviz": {"purpose": "Computer-vision inference subsystem (classification/CV)","entry":"python -m mem20cviz --help","owner":"mem20-renovation","wave":4},
    "mem20factoryz": {"purpose": "GameFactory-3A absorption (procgen, asset synthesis, level generation)","entry":"python -m mem20factoryz --help","owner":"mem20-renovation","wave":4},
    "mem20gamez": {"purpose": "OpenGame absorption (game agents, environments, reward shaping)","entry":"python -m mem20gamez --help","owner":"mem20-renovation","wave":4},
    "mem20googlez": {"purpose": "Google ADK-style agents, tools, runners, sessions, memory, flows","entry":"python -m mem20googlez --help","owner":"mem20-renovation","wave":4},
    "mem20greenz": {"purpose": "Greenroom: stage clones of external software/sites, build originals, ship","entry":"python -m mem20greenz --help","owner":"mem20-renovation","wave":4},
    "mem20kimiz": {"purpose": "Native Kimi Agent Swarm substrate (parallel subagent fan-out)","entry":"python -m mem20kimiz --help","owner":"mem20-renovation","wave":4},
    "mem20langz": {"purpose": "Native graph substrate absorption (stateful multi-agent graphs)","entry":"python -m mem20langz --help","owner":"mem20-renovation","wave":4},
    "mem20mktz": {"purpose": "Phase 2 marketplace organs (inference/capability/service markets)","entry":"python -m mem20mktz --help","owner":"mem20-renovation","wave":4},
    "mem20ocaskz": {"purpose": "Opencode feature-ask auditor (mines opencode session database)","entry":"python -m mem20ocaskz --help","owner":"mem20-renovation","wave":4},
    "mem20orcaz": {"purpose": "OrKa-style deterministic workflow orchestration (pure stdlib port)","entry":"python -m mem20orcaz --help","owner":"mem20-renovation","wave":4},
    "mem20owebz": {"purpose": "Chat front-end + model gateway (Open WebUI + LiteLLM re-home)","entry":"python -m mem20owebz --help","owner":"mem20-renovation","wave":4},
    "mem20rpgz": {"purpose": "RPGAgent absorption (stats, combat, inventory, quests, world)","entry":"python -m mem20rpgz --help","owner":"mem20-renovation","wave":4},
    "mem20sensorz": {"purpose": "Phase 1 sense-organs (capability gap, replanning, sensing)","entry":"python -m mem20sensorz --help","owner":"mem20-renovation","wave":4},
    "mem20ucgz": {"purpose": "RM-001 Universal Capability Graph (typed capability graph)","entry":"python -m mem20ucgz --help","owner":"mem20-renovation","wave":4},
    "mem20unikitz": {"purpose": "UniKit AI absorption (behavior trees, GOAP, utility AI, navigation)","entry":"python -m mem20unikitz --help","owner":"mem20-renovation","wave":4},
    "mem20unitiz": {"purpose": "Reinforcement-learning toolkit (grid envs, PPO, DQN, SAC)","entry":"python -m mem20unitiz --help","owner":"mem20-renovation","wave":4},
    "mem20wasmz": {"purpose": "WebAssembly component lab (language-neutral component compatibility)","entry":"python -m mem20wasmz --help","owner":"mem20-renovation","wave":4},
    "mem20yetiz": {"purpose": "Yeti Claw absorption (3D rigging, animation, BVH mocap, glTF)","entry":"python -m mem20yetiz --help","owner":"mem20-renovation","wave":4},
    "mem20zimr": {"purpose": "RM-002 Zero-Install Microapp Runtime (signed microapps)","entry":"python -m mem20zimr --help","owner":"mem20-renovation","wave":4},
    "mem20alternativedatabaseplaygroundz": {"purpose": "Alternative database playground (query planning, indexing, engine comparison)","entry":"python -m mem20alternativedatabaseplaygroundz --help","owner":"mem20-renovation","wave":4},
    "mem20ambientdevicecompanionz": {"purpose": "Ambient device companion (context sensing, proactive suggestions, routines)","entry":"python -m mem20ambientdevicecompanionz --help","owner":"mem20-renovation","wave":4},
    "mem20ambientteamradioz": {"purpose": "Ambient team radio (channels, messaging, routing, activity)","entry":"python -m mem20ambientteamradioz --help","owner":"mem20-renovation","wave":4},
    "mem20simz": {"purpose": "Architecture simulation sandbox (load, scaling, cost, bottlenecks, chaos)","entry":"python -m mem20simz --help","owner":"mem20-renovation","wave":4},
    "mem20assetremixstudioz": {"purpose": "Asset remix studio (remix, transform, export, blend, variants)","entry":"python -m mem20assetremixstudioz --help","owner":"mem20-renovation","wave":4},
    "mem20asynccollaborationcapsulesz": {"purpose": "Async collaboration capsules (changes, sync, merge, checksums)","entry":"python -m mem20asynccollaborationcapsulesz --help","owner":"mem20-renovation","wave":4},
    "mem20autonomoustrafficcontrollerz": {"purpose": "Autonomous traffic controller (token/leaky bucket throttling)","entry":"python -m mem20autonomoustrafficcontrollerz --help","owner":"mem20-renovation","wave":4},
    "mem20batteryawareagentschedulerz": {"purpose": "Battery-aware agent scheduler (energy-aware scheduling)","entry":"python -m mem20batteryawareagentschedulerz --help","owner":"mem20-renovation","wave":4},
    "mem20crdtcollaborationenginez": {"purpose": "CRDT collaboration engine (GCounter, PNCounter conflict-free state)","entry":"python -m mem20crdtcollaborationenginez --help","owner":"mem20-renovation","wave":4},
    "mem20dynamicphasereplannerz": {"purpose": "Dynamic phase replanner (adaptive phase planning)","entry":"python -m mem20dynamicphasereplannerz --help","owner":"mem20-renovation","wave":4},
    "mem20milestoneriskpredictorz": {"purpose": "Milestone risk predictor (schedule/risk forecasting)","entry":"python -m mem20milestoneriskpredictorz --help","owner":"mem20-renovation","wave":4},
    "mem20prioritycollisionresolverz": {"purpose": "Priority collision resolver (conflict/priority arbitration)","entry":"python -m mem20prioritycollisionresolverz --help","owner":"mem20-renovation","wave":4},
    "mem20zerodowntimemigrationbrainz": {"purpose": "Zero-downtime migration brain (verified migration orchestration)","entry":"python -m mem20zerodowntimemigrationbrainz --help","owner":"mem20-renovation","wave":4},
}


def registered_subsystems() -> dict:
    """Return the subsystem registry, for the MCP server and for operators."""
    return SUBSYSTEMS


def subsystem_entry(name: str) -> dict:
    """Look one subsystem up. Returns an explicit miss rather than None."""
    record = SUBSYSTEMS.get(name)
    if record is None:
        return {"name": name, "registered": False}
    return {"name": name, "registered": True, **record}


def ensure_dirs():
    GATEWAY_DIR.mkdir(parents=True, exist_ok=True)

def register_agent(name: str = None, location: str = None) -> dict:
    """
    Each mem20 agent picks a name on startup. If no name given, generate one.
    Returns agent record.
    """
    ensure_dirs()
    
    if not name:
        # Generate a distinctive name based on location + uuid
        loc = location or "unknown"
        short_loc = loc.replace("/", "-").replace(" ", "-")[:20]
        agent_id = uuid.uuid4().hex[:8]
        name = f"mem20-{short_loc}-{agent_id}"
    
    record = {
        "name": name,
        "location": location or "local",
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "agent_id": uuid.uuid4().hex[:8],
        "status": "active"
    }
    
    # Load existing names, check for collisions
    names = load_names()
    if name in names:
        # Append suffix to avoid collision
        base = name
        counter = 1
        while name in names:
            name = f"{base}-{counter}"
            counter += 1
        record["name"] = name
        record["collision_avoided"] = True
    
    names[name] = record
    
    with open(NAMES_FILE, "w") as f:
        json.dump(names, f, indent=2)
    
    print(f"Agent registered: {name}")
    print(f"  Location: {record['location']}")
    print(f"  Agent ID: {record['agent_id']}")
    print(f"  Registered: {record['registered_at']}")
    
    return record

def load_names() -> dict:
    if NAMES_FILE.exists():
        with open(NAMES_FILE) as f:
            return json.load(f)
    return {}

def list_agents() -> dict:
    """List all registered agents."""
    names = load_names()
    if not names:
        print("No agents registered.")
        return names
    
    print(f"Registered agents ({len(names)}):")
    for name, info in sorted(names.items()):
        status = info.get("status", "unknown")
        location = info.get("location", "unknown")
        registered = info.get("registered_at", "unknown")
        print(f"  {name}")
        print(f"    Location: {location}")
        print(f"    Status: {status}")
        print(f"    Since: {registered}")
        print()
    
    return names

def broadcast(message: str, agent_name: str = None, target: str = "telegram_channel"):
    """
    Broadcast a message to the gateway. All mem20 agents can read it.
    """
    ensure_dirs()
    
    names = load_names()
    
    if not agent_name:
        # Try to find our name
        if len(names) == 1:
            agent_name = list(names.keys())[0]
        elif len(names) > 1:
            print("Multiple agents registered. Specify --agent-name.")
            sys.exit(1)
        else:
            print("No agents registered. Run register first.")
            sys.exit(1)
    
    if agent_name not in names:
        print(f"Agent '{agent_name}' not registered. Register first.")
        sys.exit(1)
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "agent_id": names[agent_name].get("agent_id", ""),
        "location": names[agent_name].get("location", "unknown"),
        "message": message,
        "target": target,
        "source": "mem20_gateway",
        "message_id": uuid.uuid4().hex[:12]
    }
    
    with open(MESSAGES_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    print(f"Broadcast from {agent_name}: {message[:80]}...")
    return entry

def read_messages(since: str = None, agent: str = None, limit: int = 50):
    """
    Read messages from the gateway.
    """
    ensure_dirs()
    
    if not MESSAGES_FILE.exists():
        print("No messages yet.")
        return []
    
    messages = []
    with open(MESSAGES_FILE) as f:
        for line in f:
            entry = json.loads(line.strip())
            messages.append(entry)
    
    # Filter
    if agent:
        messages = [m for m in messages if m["agent"] == agent]
    
    if since:
        messages = [m for m in messages if m["timestamp"] >= since]
    
    # Sort by timestamp, newest first
    messages.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Limit
    messages = messages[:limit]
    
    if not messages:
        print("No matching messages.")
        return messages
    
    print(f"Messages ({len(messages)}):")
    for m in messages:
        print(f"  [{m['timestamp']}] {m['agent']}: {m['message'][:100]}")
    
    return messages

def parse_args():
    parser = argparse.ArgumentParser(description="mem20 Gateway — multi-mem20 relay")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # register
    p_register = subparsers.add_parser("register", help="Register this mem20 agent")
    p_register.add_argument("--name", "-n", help="Agent name (auto-generated if not provided)")
    p_register.add_argument("--location", "-l", help="VPS location or hostname")
    
    # list
    subparsers.add_parser("list", help="List all registered agents")
    
    # broadcast
    p_broadcast = subparsers.add_parser("broadcast", help="Broadcast a message")
    p_broadcast.add_argument("message", help="Message to broadcast")
    p_broadcast.add_argument("--agent-name", "-a", help="Your agent name")
    p_broadcast.add_argument("--target", "-t", default="telegram_channel", help="Target channel")
    
    # read
    p_read = subparsers.add_parser("read", help="Read messages from gateway")
    p_read.add_argument("--since", help="Only messages since this ISO timestamp")
    p_read.add_argument("--agent", "-a", help="Filter by agent name")
    p_read.add_argument("--limit", "-l", type=int, default=50, help="Max messages to return")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.command == "register":
        record = register_agent(name=args.name, location=args.location)
        print(json.dumps(record, indent=2))
    
    elif args.command == "list":
        list_agents()
    
    elif args.command == "broadcast":
        broadcast(args.message, agent_name=args.agent_name, target=args.target)
    

    elif args.command == "read":
        read_messages(since=args.since, agent=args.agent, limit=args.limit)

if __name__ == "__main__":
    main()
