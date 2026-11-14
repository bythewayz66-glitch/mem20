# mem20autonomousrecoverydirectorz — depth-first delivery record
Purpose: triage incidents, plan rollbacks, remediate safely, estimate recovery, assess post-recovery health.
Peers (6, recovery-specific): mem20faultcontainmentcellsz (containment/circuit), mem20selfhealingplansz (healing plans), mem20universalhealthnervoussystemz (health signals), mem20pipez (version/recover/vc_health), mem20eventstreamsuperhighwayz (incident events), mem20zerotouchnodeswarmz (swarm/quorum). Failures reported, never fatal.
Stack: domain+ecosystem, SQLite WAL runtime, JSON HTTP API + served web cockpit, CLI, docs/app, gateway, real MCP.
