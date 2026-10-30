"""Multi-brand swarm: brand agents, campaigns, coordination."""
import time


def create_swarm(brands):
    return {"brands": {b: {"agents": [], "campaigns": []} for b in brands}, "shared_assets": []}


def add_agent(swarm, brand, agent):
    if brand in swarm["brands"]:
        swarm["brands"][brand]["agents"].append(agent)
    return swarm


def launch_campaign(swarm, brand, campaign):
    if brand in swarm["brands"]:
        swarm["brands"][brand]["campaigns"].append({"name": campaign, "status": "running", "started": time.time()})
    return swarm


def cross_promote(swarm, brands, asset):
    for b in brands:
        if b in swarm["brands"]:
            swarm["brands"][b]["campaigns"].append({"name": f"promo:{asset}", "status": "running", "started": time.time()})
    swarm["shared_assets"].append(asset)
    return swarm


def swarm_health(swarm):
    total_agents = sum(len(b["agents"]) for b in swarm["brands"].values())
    total_camps = sum(len(b["campaigns"]) for b in swarm["brands"].values())
    return {"brands": len(swarm["brands"]), "agents": total_agents, "campaigns": total_camps}
