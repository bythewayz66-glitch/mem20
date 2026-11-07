import importlib
from .domain import daily_energy, energy_budget, evaluate, optimize_power, power_reading, threshold_check
__all__=["daily_energy","energy_budget","evaluate","optimize_power","power_reading","threshold_check","FoundationService","ecosystem"]
def __getattr__(name):
    if name=="FoundationService": return importlib.import_module(".service",__name__).FoundationService
    if name=="ecosystem": return importlib.import_module(".ecosystem",__name__)
    raise AttributeError(name)
