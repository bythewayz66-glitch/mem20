# Upgrade Proposal — what every mem20 package should actually be

**Why this document exists.** An audit hashed all 293 `mem20*z` packages with each package's own name normalised out. Only **65 distinct implementations** exist, and **228 packages are redundant clones** of just three templates (94 copies of a 273-line runtime, 93 of a 683-line runtime, 44 of a 348-line runtime). Every clone in a group is byte-identical to its siblings apart from its own name.

So a package called *adaptive pricing brain* currently contains no pricing brain. It contains the same generic runtime as 93 unrelated names. The names promise capabilities that do not exist, and that gap is invisible until you open two of them side by side.

This document says, in plain English, what each of the 231 clones should **be** — its purpose, the one thing it must refuse to do, and what would prove it works. It is a specification to build against, not a description of what is currently there.

**On grouping.** The families below are the groupings derived during the clone
audit, and they are the groupings these packages should be built against. They
turned 231 opaque names into a navigable map, which is the whole point: the
audit proved the packages are interchangeable, so the way to give them identity
is to say which family each one genuinely belongs to and build only that.

Note that the `Sherry`/`Judy`/`Jammee` names in the clone template's
`FAMILY_FUNCS` are not a family plan — that is the dispatch table of the generic
runtime, duplicated 231 times, and is part of the problem this document fixes.

**Three rules for every package below.**

1. **Do one thing.** A package that can do three jobs does none of them well and cannot be tested for any of them.
2. **Refuse rather than fake.** Unknown input, unsupported request, or a confidence below threshold must produce an explicit refusal — never a plausible-looking wrong answer.
3. **Prove it with a test that could fail.** A test asserting the function returns something is worthless. Assert a known value, a bound, or a contradiction.

---

## Priority

Build in leverage order, not name order.

Building these in name order wastes effort on low-value packages. Better to go by leverage:

| Tier | Meaning | Rough size |
|---|---|---|
| **A** | Read by other packages — build these first | 30% small, 60% average |
| **B** | High-value capability, self-contained | 10% extra large |
| **C** | Speculative, duplicates something in A or B | defer until needed |

---

## Networking & transport  (17 packages)

**What this family is for.** Moving messages and bytes correctly under failure, duplication and reordering.

### `mem20ambientteamradioz`

- **Should be:** radio — low-bandwidth communication that still carries meaning.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20conversationalactiondesktopz`

- **Should be:** conversational desktop — operate by conversation with a confirmation step.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crossdevicesessioncontinuityz`

- **Should be:** cross-device — state follows the person, not the device.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20edgefleetbrainz`

- **Should be:** edge fleet — manage a fleet whose nodes are unreliable by definition.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20edgetocloudintelligencecontinuumz`

- **Should be:** edge-to-cloud continuum — run work where it is cheapest to run, not where it is easiest.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20edgetransportfabricz`

- **Should be:** fabric — the transport underneath, with backpressure that is measurable.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20eventstreamsuperhighwayz`

- **Should be:** event stream — ordered delivery with replay, or an explicit statement that it is not.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20freestackambientcomputingfabricz`

- **Should be:** fabric — the transport underneath, with backpressure that is measurable.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20mobileedgeagentruntimez`

- **Should be:** mobile edge runtime — run locally when the link is bad, remotely when it is good.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20nearbydevicemeshz`

- **Should be:** mesh — peer connections that survive any single node failing.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20planetarybatchfabricz`

- **Should be:** fabric — the transport underneath, with backpressure that is measurable.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20presenceawarecommunicationshubz`

- **Should be:** hub — the place connections meet, designed so its failure is survivable.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20realtimeeventautopilotz`

- **Should be:** event autopilot — react to events without a human in the loop, within stated bounds.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20realtimeteampresencez`

- **Should be:** presence — know who is available without polling.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20sensorfusiongatewayz`

- **Should be:** gateway — translate between callers and backends without losing either contract.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20voicetoactionswitchboardz`

- **Should be:** voice-to-action — turn a spoken intent into a verified action.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20webhooksupernetworkz`

- **Should be:** webhook — deliver exactly once, and prove it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Compilation & code generation  (15 packages)

**What this family is for.** Turning a stated intent into something that runs. Each must refuse cleanly when the intent cannot be compiled.

### `mem20agentoutputcompilerz`

- **Should be:** compiler — turn a declared intent into something that runs, or say it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20apishapeshiftinggatewayz`

- **Should be:** API shape translation — adapt a caller's shape to a provider's shape without leaking either.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autogeneratedprototypepathz`

- **Should be:** prototype path — generate a prototype that is honest about being a prototype.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20contextcompressionforgez`

- **Should be:** context compression — cut context losslessly where possible, lossy only where declared.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crosslanguagerefactorenginez`

- **Should be:** cross-language refactor — change behaviour identically across languages.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20deterministicconfigurationgraphz`

- **Should be:** deterministic config — the same inputs always produce the same running system.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20devicecapabilitycompilerz`

- **Should be:** compiler — turn a declared intent into something that runs, or say it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20executableroadmapcompilerz`

- **Should be:** compiler — turn a declared intent into something that runs, or say it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20featuredependencygraphenginez`

- **Should be:** feature dependency — know what breaks when a flag changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20intentcompilerz`

- **Should be:** compiler — turn a declared intent into something that runs, or say it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20intenttoagentmatchmakerz`

- **Should be:** intent-to-agent matching — match a stated goal to an agent that can actually achieve it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20intenttomissioncompilerz`

- **Should be:** compiler — turn a declared intent into something that runs, or say it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20realitytosoftwarecompilerz`

- **Should be:** compiler — turn a declared intent into something that runs, or say it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20realworldimpactrewardsz`

- **Should be:** impact reward — reward what actually changed for a person, not what was shipped.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20universalintegrationcompilerz`

- **Should be:** compiler — turn a declared intent into something that runs, or say it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Business & growth  (14 packages)

**What this family is for.** Turning an idea into something a customer pays for, measured against an outcome.

### `mem20acquisitionandpartnershipscoutz`

- **Should be:** scout — gather options with sources, so the choice is auditable.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20aigamestudiobuilderz`

- **Should be:** AI game studio — produce a playable game, not a design document.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20ailevelarchitectz`

- **Should be:** AI level architect — design a level that is fun, proven by simulating play.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20aipipelinecostoptimizerz`

- **Should be:** pipeline cost optimiser — know what each pipeline step costs before running it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomousdealdeskz`

- **Should be:** deal desk — qualify and progress a deal without a human re-reading it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomousmicrosaasfoundryz`

- **Should be:** micro-SaaS foundry — find and launch the smallest thing that is genuinely useful.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomoussaleslaboratoryz`

- **Should be:** sales lab — test a pitch against real objections before it reaches a customer.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomoussoftwarefoundryz`

- **Should be:** software foundry — take an idea to working software with a test at every step.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crossplatformmicrokernelz`

- **Should be:** microkernel — the smallest trusted core everything else defers to.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20customerlifecycleenginez`

- **Should be:** customer lifecycle — know where a customer is and what they need next.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20gameproductioncontrolcenterz`

- **Should be:** production control — a control room view that cannot lie about state.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20generativebrandworldenginez`

- **Should be:** brand — a voice consistent enough to be recognised.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20interactivecampaignbuilderz`

- **Should be:** campaign — a campaign measured against an outcome, not against impressions.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multibrandswarmz`

- **Should be:** brand — a voice consistent enough to be recognised.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Simulation & twins  (14 packages)

**What this family is for.** Running a scenario and reading a number. These are worthless if they produce a vibe instead of a measurement.

### `mem20audiencereactionsimulatorz`

- **Should be:** simulator — run a scenario and read a number, not a vibe.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20businessmodelsimulatorz`

- **Should be:** simulator — run a scenario and read a number, not a vibe.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20conflictdeescalationassistantz`

- **Should be:** de-escalation — reduce a conflict measurably, not politely.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crisisresponsemeshz`

- **Should be:** crisis response — the first actions under pressure, decided before the pressure.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20gamebalancesimulatorz`

- **Should be:** simulator — run a scenario and read a number, not a vibe.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20humansatisfactiontwinz`

- **Should be:** digital twin — a live model that tracks a real thing and is wrong when it changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20leveldesignworldbuildingandnavigationpipelinez`

- **Should be:** level design — a level that navigates well, proven by walking it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20operationsreplaysimulatorz`

- **Should be:** simulator — run a scenario and read a number, not a vibe.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20personalworkflowtwinz`

- **Should be:** digital twin — a live model that tracks a real thing and is wrong when it changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20playermotivationtwinz`

- **Should be:** digital twin — a live model that tracks a real thing and is wrong when it changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20productledgrowthsimulatorz`

- **Should be:** simulator — run a scenario and read a number, not a vibe.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20realtimebusinesstwinz`

- **Should be:** digital twin — a live model that tracks a real thing and is wrong when it changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20spatialcomputingsandboxz`

- **Should be:** sandbox — an isolation boundary that is tested by trying to escape it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20useracceptancesimulatorz`

- **Should be:** simulator — run a scenario and read a number, not a vibe.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Coordination primitives  (13 packages)

**What this family is for.** The plumbing that makes several actors safe to run together. Almost all of these fail in the same way: silently, and only under concurrency.

### `mem20asynccollaborationcapsulesz`

- **Should be:** async capsules — a unit of work that survives being picked up by someone else.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomoustrafficcontrollerz`

- **Should be:** traffic control — shape live traffic against real capacity, not a guess.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomousworkcellsz`

- **Should be:** work cell — a self-contained unit of capacity that can be scheduled as one thing.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20causalroutingbrainz`

- **Should be:** causal routing — route on cause, not on correlation.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crdtcollaborationenginez`

- **Should be:** CRDT collaboration — merge concurrent edits without a lock and without a lost update.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20demandforecastandcapacitybrainz`

- **Should be:** demand forecast — predict demand with an interval, and be honest when the data is thin.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20dependencymutationlabz`

- **Should be:** mutation lab — change one thing and observe, in a lab not a production.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20milestoneriskpredictorz`

- **Should be:** milestone risk — say a milestone is at risk while there is still time to act.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20outcomeverificationruntimez`

- **Should be:** outcome verification — check the claimed outcome against the world, not the log.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20qualityriskforecasterz`

- **Should be:** quality risk forecast — rank risk by consequence times likelihood, not by volume of worry.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20reversibleexecutiongraphz`

- **Should be:** reversible execution — undo in reverse order, provably.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20runtimebugpredictionenginez`

- **Should be:** bug prediction — predict where this change will break, from history.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20zerotouchnodeswarmz`

- **Should be:** zero-touch node — a node that maintains itself and says so when it cannot.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Resilience & self-repair  (13 packages)

**What this family is for.** Systems that notice they are broken and fix it. The hard part is proving the fix held rather than assuming it.

### `mem20autonomousrecoverydirectorz`

- **Should be:** recovery orchestration — sequence the restoration so the dependency order is respected.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20continuouscompatibilitylabz`

- **Should be:** compatibility — detect incompatibility before it reaches a user.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20faultcontainmentcellsz`

- **Should be:** fault containment — stop a failure spreading past its blast radius.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20hotswappableservicefoundationz`

- **Should be:** hot swap — replace a component live without invalidating callers.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20offlineresiliencemeshz`

- **Should be:** offline resilience — keep working when the network does not, and reconcile later.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20releasereadinesspredictorz`

- **Should be:** release readiness — predict whether a build is safe to ship, from measured evidence.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20remotedevicerepairz`

- **Should be:** remote repair — diagnose and fix a device you cannot physically touch.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20runtimecompatibilityenginez`

- **Should be:** compatibility — detect incompatibility before it reaches a user.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20selfhealingconnectormeshz`

- **Should be:** self-healing — detect its own degradation and recover without being told.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20selfhealingplansz`

- **Should be:** self-healing — detect its own degradation and recover without being told.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20selfhealingruntimecivilizationz`

- **Should be:** self-healing — detect its own degradation and recover without being told.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20selfrepairingtestfactoryz`

- **Should be:** self-repair — repair the damage it finds, and prove the repair held.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20zerodowntimemigrationbrainz`

- **Should be:** zero-downtime change — swap a live component with no dropped request.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Orchestration & planning  (12 packages)

**What this family is for.** Deciding what runs, in what order, with what fallback. A plan that cannot survive a member failing is not a plan.

### `mem20adaptivedispatchenginez`

- **Should be:** dispatch — send each task to the agent best able and available to take it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20batteryawareagentschedulerz`

- **Should be:** scheduler — decide what runs when, and prove the schedule is feasible.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crossruntimeeventlatticez`

- **Should be:** event lattice — route events across runtimes with ordering that survives failure.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20dynamicphasereplannerz`

- **Should be:** dynamic replanner — re-plan mid-flight when reality diverges from the plan.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20goaleconomyschedulerz`

- **Should be:** scheduler — decide what runs when, and prove the schedule is feasible.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20goapagentdesignerz`

- **Should be:** GOAP — plan by goal and precondition, so an impossible goal is refused not attempted.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20locationawareworkrouterz`

- **Should be:** location-aware routing — send work to where the resource actually is.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20missionroutingcockpitz`

- **Should be:** mission routing — route a mission to the capability that fits, with a fallback.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multichannelcommandstreamz`

- **Should be:** command stream — one command, many channels, one consistent outcome.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20productionplanningandtaskorchestrationpipelinez`

- **Should be:** task orchestration — a plan with dependencies that survives a member failing.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20realtimeexecutionmapz`

- **Should be:** execution map — the live picture of what is executing right now.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20roamingworkloadschedulerz`

- **Should be:** scheduler — decide what runs when, and prove the schedule is feasible.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Markets & economics  (12 packages)

**What this family is for.** Matching supply and demand, and pricing from measured behaviour. Publish the rule before running it.

### `mem20communitychallengeenginez`

- **Should be:** community — participation measured at the seam, not counted at signup.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20communitypulseenginez`

- **Should be:** community — participation measured at the seam, not counted at signup.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20compoundingproductecosystemz`

- **Should be:** ecosystem — model the system, not just the parts in it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20connectormarketplacez`

- **Should be:** marketplace — match supply and demand at a price that clears.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crossproductloyaltygraphz`

- **Should be:** loyalty graph — measure what actually brings someone back.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20hardwaremarketplacez`

- **Should be:** marketplace — match supply and demand at a price that clears.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20livingagenteconomyz`

- **Should be:** economy — model incentives so the honest choice is also the profitable one.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20offerassemblyfabricz`

- **Should be:** offer assembly — assemble an offer from parts without it becoming incoherent.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20offergenomeenginez`

- **Should be:** offer genome — the structural parts of an offer, so variants can be reasoned about.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20opportunityradarz`

- **Should be:** opportunity radar — surface opportunities ranked by evidence, not enthusiasm.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20resourceexchangemarketz`

- **Should be:** exchange — clear trades fairly, with the rule published before it runs.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20revenueleakhunterz`

- **Should be:** revenue leak hunter — find money leaving the business and show where.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Interfaces & modality  (12 packages)

**What this family is for.** Getting meaning in and out of the system in whatever form it arrives. The failure mode is claiming to understand a modality it silently ignored.

### `mem20emotionsensitivemessagerouterz`

- **Should be:** emotion-sensitive router — route by tone without pretending to diagnose.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20instantappsynthesisz`

- **Should be:** instant app — synthesise a small working app from a stated need.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20modalitybridgez`

- **Should be:** modality bridge — move meaning between representations without losing it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multidevicecompletioncheckerz`

- **Should be:** multi-device completion — finish the task wherever it started.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multilingualliveconversationenginez`

- **Should be:** multilingual handling — work in the user's language without translating them into a worse one.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multimodaltaskcapturez`

- **Should be:** task capture — understand what the user wants from a gesture, a voice or a glance.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multimodalunderstandingcorez`

- **Should be:** multimodal understanding — read text, image and audio as one input, and say which it used.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20privatelocalreasoningenginez`

- **Should be:** private local reasoning — reason on-device so the data never leaves.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20specialistmodelforgez`

- **Should be:** specialist model forge — distil a narrow model and show it beats the generalist on its task.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20visualagentblackboardz`

- **Should be:** agent blackboard — shared inspectable state for agents working together.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20webassemblycomponentlabz`

- **Should be:** WebAssembly component — a sandboxed component that runs the same everywhere.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20webgpucomputestudioz`

- **Should be:** WebGPU compute — real GPU work in the browser, with a CPU fallback that is honest.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Memory & cognition  (11 packages)

**What this family is for.** retrieval, consolidation and recall over a store it does not own; what happened, when, in order — an event log with replay and branching; what would have followed from a different choice, scored for plausibility; anticipate what a query will need and prefetch it before it is asked

### `mem20counterfactualmemorysimulatorz`

- **Should be:** long-term memory — retrieval, consolidation and recall over a store it does not own.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20crossdevicememorymeshz`

- **Should be:** long-term memory — retrieval, consolidation and recall over a store it does not own.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20dynamicskillgraphz`

- **Should be:** dynamic skill graph — skills as a graph with prerequisites, so a gap blocks and a path completes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20episodicmemorygraphz`

- **Should be:** long-term memory — retrieval, consolidation and recall over a store it does not own.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20livecodeknowledgegraphz`

- **Should be:** live code knowledge graph — the graph updates as the code changes, not on a manual refresh.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20memorytimemachinez`

- **Should be:** long-term memory — retrieval, consolidation and recall over a store it does not own.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20predictiverecallenginez`

- **Should be:** predictive recall — anticipate what a query will need and prefetch it before it is asked.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20relationshipcontextgraphz`

- **Should be:** relationship graph — who is connected to whom, and how that connection changes over time.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20semanticobjectgraphz`

- **Should be:** semantic object graph — objects and their relations as a queryable graph, not a blob of text.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20sensorymemoryingestz`

- **Should be:** long-term memory — retrieval, consolidation and recall over a store it does not own.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20skillmemorytransferz`

- **Should be:** long-term memory — retrieval, consolidation and recall over a store it does not own.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Media & generation  (10 packages)

**What this family is for.** story that holds together across a long arc; keep audio and image in step, measurably; motion that lands on the beat and holds a silhouette; produce assets under a real budget, not an aspiration

### `mem202dand3dartproductionoptimizationpipelinez`

- **Should be:** 3D pipeline — geometry that survives export, import and re-edit.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20assetintakecatalogingandvalidationpipelinez`

- **Should be:** asset pipeline — produce assets under a real budget, not an aspiration.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20assetremixstudioz`

- **Should be:** asset pipeline — produce assets under a real budget, not an aspiration.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20creativetrendradarz`

- **Should be:** creative direction — a coherent style held across many assets.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20dynamicnarrativeenginez`

- **Should be:** narrative — story that holds together across a long arc.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multimodalcreativedirectorz`

- **Should be:** creative direction — a coherent style held across many assets.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20musicvisualsynchronizerz`

- **Should be:** music-visual sync — keep audio and image in step, measurably.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20narrativedialogueandlocalizationpipelinez`

- **Should be:** narrative — story that holds together across a long arc.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20rigginganimationandmotionpipelinez`

- **Should be:** rigging & animation — motion that lands on the beat and holds a silhouette.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20versioncontrollargeassetandrecoverypipelinez`

- **Should be:** asset pipeline — produce assets under a real budget, not an aspiration.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Coordination & multi-agent  (10 packages)

**What this family is for.** assign work to agents that are free and actually good at it; hunt for the failure on purpose and report it before a user finds it; make a bounded edit, prove it, and revert cleanly when it does not hold; several independent reviewers, disagreements surfaced rather than averaged

### `mem20adversarialqacrewz`

- **Should be:** adversarial QA crew — hunt for the failure on purpose and report it before a user finds it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomouscodesurgeonz`

- **Should be:** code surgery — make a bounded edit, prove it, and revert cleanly when it does not hold.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20autonomousreviewswarmz`

- **Should be:** review swarm — several independent reviewers, disagreements surfaced rather than averaged.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20capabilitymarketplacez`

- **Should be:** capability marketplace — match a need to a capability by measured fit, not by name.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20federatedmodellearningmeshz`

- **Should be:** federated learning — learn across participants without centralising anyone's data.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20federatedresearchgridz`

- **Should be:** federated learning — learn across participants without centralising anyone's data.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20globalcapabilitymarketplacez`

- **Should be:** capability marketplace — match a need to a capability by measured fit, not by name.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20parallelworkstreamcomposerz`

- **Should be:** parallel workstreams — run independent tracks and merge only where they genuinely meet.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20peertopeerappruntimez`

- **Should be:** peer runtime — agent-to-agent work with clear ownership and a shared, honest view of state.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20prioritycollisionresolverz`

- **Should be:** priority collision resolver — when two things want the same resource, resolve it visibly and reversibly.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Simulation & modelling  (10 packages)

**What this family is for.** a model you can run and probe, not a diagram; a live model that tracks a real thing and is wrong when the thing changes; run plausible futures and show which decisions are robust across them; inject faults deliberately and prove the system degrades the way it claims

### `mem20architecturesimulationsandboxz`

- **Should be:** simulation — a model you can run and probe, not a diagram.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20chaosnativeapplicationruntimez`

- **Should be:** chaos runtime — inject faults deliberately and prove the system degrades the way it claims.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20customerdigitaltwinlabz`

- **Should be:** digital twin — a live model that tracks a real thing and is wrong when the thing changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20executiondigitaltwinz`

- **Should be:** digital twin — a live model that tracks a real thing and is wrong when the thing changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20integrationdigitaltwinz`

- **Should be:** digital twin — a live model that tracks a real thing and is wrong when the thing changes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20lifescenariosimulatorz`

- **Should be:** scenario simulation — run plausible futures and show which decisions are robust across them.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20multiworldsandboxz`

- **Should be:** multi-world sandbox — explore branches without letting one contaminate another.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20outcomesimulationlabz`

- **Should be:** simulation — a model you can run and probe, not a diagram.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20roadmapsimulationtwinz`

- **Should be:** simulation — a model you can run and probe, not a diagram.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20scopemutationsandboxz`

- **Should be:** scope mutation sandbox — try risky edits in a sandbox that cannot reach production.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Learning & adaptation  (9 packages)

**What this family is for.** decay a memory by how it is actually used, and schedule when to revisit it; a stable disposition that shifts under repeated pressure but does not thrash; track real progress toward a goal and refuse credit for unearned progress; estimate demand elasticity from observed behaviour and price accordingly

### `mem20adaptiveachievementenginez`

- **Should be:** achievement engine — track real progress toward a goal and refuse credit for unearned progress.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20adaptiveforgettingenginez`

- **Should be:** adaptive forgetting — decay a memory by how it is actually used, and schedule when to revisit it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20adaptivepersonalityruntimez`

- **Should be:** personality runtime — a stable disposition that shifts under repeated pressure but does not thrash.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20adaptivepricingbrainz`

- **Should be:** pricing brain — estimate demand elasticity from observed behaviour and price accordingly.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20continuousimprovementloopz`

- **Should be:** improvement loop — hypothesise, test, keep or revert — never adopt an unmeasured change.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20performanceregressionhunterz`

- **Should be:** regression hunter — catch a slowdown before it ships, by comparing against a recorded baseline.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20runtimepromptoptimizerz`

- **Should be:** prompt optimiser — improve a prompt against measured outcomes, not vibes.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20safepatchsynthesisz`

- **Should be:** safe patch synthesis — propose a fix that passes the tests, or produce nothing.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20selfoptimizingkernelz`

- **Should be:** self-optimising kernel — retune itself against a measured objective, with a hard ceiling on drift.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## User & experience  (9 packages)

**What this family is for.** measure the experience, do not describe it; see Learning & adaptation; decide what deserves attention now and defend that decision; control expressed in the space the user is actually in

### `mem20ambientdevicecompanionz`

- **Should be:** companion — present without demanding attention.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20dailydecisioncopilotz`

- **Should be:** copilot — assist without taking over, and be ignored without complaint.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20experiencefrictiondetectorz`

- **Should be:** experience design — measure the experience, do not describe it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20mixedinitiativefocusenginez`

- **Should be:** focus engine — decide what deserves attention now and defend that decision.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20personalintelligencecompanionz`

- **Should be:** companion — present without demanding attention.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20smartmeetingcopilotz`

- **Should be:** copilot — assist without taking over, and be ignored without complaint.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20spatialcommanduniversez`

- **Should be:** spatial command — control expressed in the space the user is actually in.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20spatialexperiencedesignerz`

- **Should be:** experience design — measure the experience, do not describe it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20universalcompaniondevicesdkz`

- **Should be:** companion — present without demanding attention.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Experimentation & reward  (9 packages)

**What this family is for.** Measuring, scoring and shaping. A reward that can be gamed has not been measured, it has been exploited.

### `mem20capabilitygapmapperz`

- **Should be:** capability gap mapper — show precisely what is missing between wanted and available.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20completionconfidenceenginez`

- **Should be:** completion confidence — say how sure the system is, and be calibrated about it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20dynamicquestrewardcomposerz`

- **Should be:** reward composition — compose rewards so grinding does not beat playing.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20remoteexperimentlabz`

- **Should be:** remote experiment — run an experiment live with a stop condition decided in advance.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20rewardforgez`

- **Should be:** reward shaping — shape a reward without breaking policy invariance.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20selftuningresourcegovernorz`

- **Should be:** self-tuning resource governor — retune limits against measured load, within bounds.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20servicebundlingenginez`

- **Should be:** service bundling — group services so an operator can reason about the whole.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20skillbasedprogressionbrainz`

- **Should be:** skill progression — progress that reflects measured skill, not time served.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20syntheticevaluatorarenaz`

- **Should be:** synthetic evaluator — score output against a rubric, and show where the rubric fails.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Unclassified — needs a decision  (9 packages)

These names do not state a capability the audit can pin down. Give each a one-line purpose, or fold it into a sibling that already does the job honestly. Shipping a name with no meaning behind it is exactly the problem this audit found.

### `mem20collectivemodelintelligencez`

- **Should be:** collectivemodelintelligence — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20deviceenrollmentautopilotz`

- **Should be:** deviceenrollmentautopilot — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20eventshaperouterz`

- **Should be:** eventshaperouter — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20liveprojectdemonstrationenginez`

- **Should be:** liveprojectdemonstrationengine — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20liveschemamorphingenginez`

- **Should be:** liveschemamorphingengine — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20loreragcontentgeneratorz`

- **Should be:** loreragcontentgenerator — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20neuromorphiceventlabz`

- **Should be:** neuromorphiceventlab — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20realtimestyletransferpipelinez`

- **Should be:** realtimestyletransferpipeline — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20uniteconomicsautopilotz`

- **Should be:** uniteconomicsautopilot — The name does not state a capability this audit can pin down. Either give it a one-line purpose or fold it into a sibling that already does the job honestly..
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Inference & serving  (8 packages)

**What this family is for.** send each request to the cheapest backend that can actually serve it; match supply and demand for compute capacity at a clearing price; describe a model by its measured traits so a good one can be found again; shard and evict under pressure, restore exactly, prove nothing was lost

### `mem20adaptiveinferencemarketplacez`

- **Should be:** inference routing — send each request to the cheapest backend that can actually serve it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20energyawarecomputemigrationz`

- **Should be:** energy-aware scheduling — move work to when and where the power is cheap and clean.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20energyawarefoundationz`

- **Should be:** energy-aware scheduling — move work to when and where the power is cheap and clean.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20hardwareawareinferencecompilerz`

- **Should be:** hardware-aware compilation — compile a model for the silicon that will actually run it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20livemodelfusionz`

- **Should be:** model fusion — blend several models and show the blend beats each parent.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20modelgenomelabz`

- **Should be:** model genome — describe a model by its measured traits so a good one can be found again.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20modelsleepandwakesystemz`

- **Should be:** model sleep/wake — shard and evict under pressure, restore exactly, prove nothing was lost.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20speculativeworkflowenginez`

- **Should be:** speculative execution — guess ahead, verify cheaply, keep only what was right.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Human & wellbeing  (8 packages)

**What this family is for.** Working with people rather than replacing them. Every one of these must be interruptible and must accept being ignored.

### `mem20contextawarelearningcoachz`

- **Should be:** learning coach — teach by adjusting difficulty, measured not guessed.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20humanagentcoworkcanvasz`

- **Should be:** human-agent cowork — share work with a person without taking their intent.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20humancapabilityacceleratorz`

- **Should be:** human capability — map what a person can actually do, and adapt to it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20humancapabilitysuperplatformz`

- **Should be:** human capability — map what a person can actually do, and adapt to it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20personalautomationcanvasz`

- **Should be:** personal automation — automate the repetitive without automating the meaningful.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20personalcognitivesearchz`

- **Should be:** personal cognitive search — search a person's own history with consent and control.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20personalmodelevolutionz`

- **Should be:** personal model evolution — a model of a person that revises on correction.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20universalhealthnervoussystemz`

- **Should be:** health — support wellbeing decisions without diagnosing.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Studio & content production  (7 packages)

**What this family is for.** Producing work with a voice. Each must hold consistency across many outputs, which is a testable property rather than an opinion.

### `mem20aiproductionstudiooperatingsystemz`

- **Should be:** production operating system — run a whole production line with one honest state view.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20apprenticeshipruntimez`

- **Should be:** apprenticeship runtime — learn by doing under supervision, with the supervision explicit.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20audiovoiceandmusicpipelinez`

- **Should be:** audio/voice/music pipeline — produce a coherent sound bed, not unrelated stems.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20characterandmascotforgez`

- **Should be:** character forge — a character with a consistent voice and silhouette.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20protocolautodiscoveryenginez`

- **Should be:** protocol discovery — find the protocol that exists before assuming yours.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20protocolinventionstudioz`

- **Should be:** protocol invention — design a protocol and show it cannot be trivially broken.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20styleguideagentz`

- **Should be:** style guide agent — hold a visual and verbal line across many assets.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Identity, privacy & security  (4 packages)

**What this family is for.** Knowing who is asking and what they may do, without holding more authority than the task needs.

### `mem20offlineappdeliveryz`

- **Should be:** offline delivery — ship an app that works with no network and upgrades safely later.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20secretslessworkloadidentityz`

- **Should be:** secretsless identity — act without holding credentials, using short-lived scoped grants.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20securebuildtodevicepipelinez`

- **Should be:** secure build — prove the artefact came from the source it claims.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20securecomputecapsulesz`

- **Should be:** secure compute — run sensitive work where the operator cannot read it.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Trust, safety & governance  (3 packages)

**What this family is for.** make the profitable choice also the defensible one, then verify it is; assume the input is hostile and prove the guard holds; turn a described outcome into a checkable specification; a design that either runs or is wrong, with no third state

### `mem20antiexploitationrewardshieldz`

- **Should be:** exploit resistance — assume the input is hostile and prove the guard holds.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20ethicalincentivesimulatorz`

- **Should be:** ethical incentives — make the profitable choice also the defensible one, then verify it is.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20executabledesignstresslabz`

- **Should be:** executable design — a design that either runs or is wrong, with no third state.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

## Optimisation & modelling  (2 packages)

**What this family is for.** Improving a measured objective without breaking a stated constraint.

### `mem20buildsequenceoptimizerz`

- **Should be:** optimiser — improve a measured objective without breaking a constraint.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.

### `mem20quantuminspiredoptimizerz`

- **Should be:** optimiser — improve a measured objective without breaking a constraint.
- **Must refuse:** to be a general-purpose runtime, and to return a confident answer when it is out of its depth.
- **Proven by:** a test asserting a specific value, bound or contradiction — not that the function ran.
