# mem20autonomousworkcellsz — depth-first delivery record
Purpose: autonomous work cells (task queues, worker assignment, throughput, cell health).
Peers (6, workcell-specific): mem20zerotouchnodeswarmz (worker swarm/assignment/quorum), mem20capabilitymarketplacez (capability routing), mem20eventstreamsuperhighwayz (work events), mem20faultcontainmentcellsz (cell isolation/containment), mem20mixedinitiativefocusenginez (focus/priority), mem20causalroutingbrainz (capacity forecast/headroom). Reported-not-fatal.
Stack: domain+ecosystem, SQLite WAL runtime, JSON HTTP API + served web cockpit, CLI, docs/app, gateway, real MCP.
