"""Hardware-aware inference compiler: op fusion, quantization, scheduling."""
import math


def fuse_ops(ops):
    fused = []
    i = 0
    while i < len(ops):
        if i + 1 < len(ops) and ops[i].get("type") == "matmul" and ops[i+1].get("type") == "relu":
            fused.append({"type": "fused_matmul_relu", "ops": [ops[i], ops[i+1]]})
            i += 2
        else:
            fused.append(ops[i])
            i += 1
    return fused


def quantize(weights, bits=8):
    scale = (max(weights) - min(weights)) / (2**bits - 1) if weights else 1
    q = [round((w - min(weights)) / scale) for w in weights]
    return {"quantized": q, "scale": scale, "min": min(weights) if weights else 0, "bits": bits}


def schedule(ops, device):
    # sort by priority desc
    return sorted(ops, key=lambda o: -o.get("priority", 0))


def memory_estimate(ops, dtype_bytes=4):
    return sum(o.get("size", 0) for o in ops) * dtype_bytes


def optimize_graph(graph):
    nodes = graph.get("nodes", [])
    # remove identity ops
    filtered = [n for n in nodes if n.get("type") != "identity"]
    return {"nodes": filtered, "removed": len(nodes) - len(filtered)}
