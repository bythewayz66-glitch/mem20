"""Adversarial QA crew: test generation, mutation, fuzzing, verdict."""
import random, hashlib


def generate_adversarial_cases(spec, count=10):
    """Generate adversarial test cases from a spec dict."""
    cases = []
    for i in range(count):
        case = {"id": f"adv-{i}", "input": spec.get("base_input", {}), "mutation": None}
        # boundary mutations
        if i % 3 == 0:
            case["mutation"] = "boundary"
            case["input"] = {**case["input"], "value": 0}
        elif i % 3 == 1:
            case["mutation"] = "overflow"
            case["input"] = {**case["input"], "value": 10**9}
        else:
            case["mutation"] = "null"
            case["input"] = {**case["input"], "value": None}
        cases.append(case)
    return cases


def mutation_score(original, mutated):
    """Score how much a mutation changed the output (0..1)."""
    if original == mutated:
        return 0.0
    a = str(original); b = str(mutated)
    diff = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
    return round(min(1.0, diff / max(1, len(a))), 4)


def fuzz_input(base, seed=0):
    """Generate a fuzzed input variant."""
    rng = random.Random(seed)
    out = dict(base)
    for k in list(out.keys()):
        if isinstance(out[k], int):
            out[k] = out[k] + rng.randint(-5, 5)
        elif isinstance(out[k], str):
            out[k] = out[k] + chr(rng.randint(33, 126))
    return out


def verdict(results):
    """Aggregate test results into a release verdict."""
    total = len(results)
    failed = [r for r in results if not r.get("pass", False)]
    return {
        "total": total,
        "failed": len(failed),
        "release_blocked": bool(failed),
        "pass_rate": round((total - len(failed)) / max(1, total), 4),
    }


def hash_case(case):
    return hashlib.sha256(str(sorted(case.items())).encode()).hexdigest()[:12]
