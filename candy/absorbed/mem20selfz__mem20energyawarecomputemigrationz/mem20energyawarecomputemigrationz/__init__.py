"""mem20energyawarecomputemigrationz (RM-047): Energy-Aware Compute Migration."""
import importlib
from .domain import (
    ComputeNode, Workload, carbon_footprint, energy_cost, fleet_energy_summary,
    greenest_node, migrate_decision, migration_plan, plan_migrations, score_node,
)
__all__ = [
    "ComputeNode", "Workload", "MigrationService", "ValidationError",
    "carbon_footprint", "energy_cost", "fleet_energy_summary", "greenest_node",
    "migrate_decision", "migration_plan", "plan_migrations", "score_node", "ecosystem",
]
def __getattr__(name):
    if name in ("MigrationService", "ValidationError"):
        mod = importlib.import_module(".service", __name__); return getattr(mod, name)
    if name == "ecosystem":
        return importlib.import_module(".ecosystem", __name__)
    raise AttributeError(name)
