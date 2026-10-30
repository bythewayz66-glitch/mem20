"""Planetary batch fabric: distributed batch jobs across regions."""
import time, uuid


def submit_job(region, payload, priority=0):
    return {"id": str(uuid.uuid4())[:8], "region": region, "payload": payload, "priority": priority, "status": "queued", "submitted": time.time()}


def schedule(jobs, capacity):
    # greedy by priority desc
    jobs = sorted(jobs, key=lambda j: -j.get("priority", 0))
    scheduled = []
    for j in jobs:
        if capacity.get(j["region"], 0) > 0:
            capacity[j["region"]] -= 1
            j["status"] = "scheduled"
            scheduled.append(j)
    return scheduled


def job_status(job):
    return job.get("status", "unknown")


def fabric_health(regions):
    return {"regions": len(regions), "capacity": sum(regions.values())}


def retry(job, max_retries=3):
    if job.get("retries", 0) < max_retries:
        job["retries"] = job.get("retries", 0) + 1
        job["status"] = "queued"
        return {"ok": True, "retries": job["retries"]}
    return {"ok": False, "reason": "max retries"}
