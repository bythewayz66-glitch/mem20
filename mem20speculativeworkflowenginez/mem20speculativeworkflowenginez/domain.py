"""Speculative workflow engine: pre-execute likely branches."""
import time


def speculate(workflow, branches):
    results = []
    for b in branches:
        results.append({"branch": b, "status": "speculated", "result": None})
    return results


def commit(spec_results, chosen):
    for r in spec_results:
        if r["branch"] == chosen:
            r["status"] = "committed"
            r["result"] = "executed"
        else:
            r["status"] = "discarded"
    return spec_results


def rollback(spec_results):
    for r in spec_results:
        r["status"] = "rolled_back"
    return spec_results


def speculative_health(spec_results):
    committed = sum(1 for r in spec_results if r["status"]=="committed")
    return {"branches": len(spec_results), "committed": committed}
