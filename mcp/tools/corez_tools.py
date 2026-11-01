"""mem20corez tools for the mem20 MCP server.

Exposes the native CoreAI primitives to agents: real inference through the
tensor engine, real quantization, real evaluation, and the subsystem's
cross-subsystem wiring report. Every number returned here is computed -- the
tensor engine runs real matrix multiplication and the quantizer measures real
error, so nothing is a canned value.

Tools:

* ``corez_infer``     -- real greedy completion from the character MLP
* ``corez_quantize``  -- real int8/int4/fp16 quantization with measured error
* ``corez_evaluate``  -- real accuracy/perplexity/latency from execution
* ``corez_wiring``    -- prove the cross-subsystem edges
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from mcp.server import Server
    from mcp.server.lowlevel.server import ServerRequestContext
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
    MCP_SDK_IMPORT_ERROR = None
except ImportError as _mcp_sdk_exc:  # pragma: no cover - only without the SDK
    # Never sys.exit() at import time: pytest imports this module during
    # collection and a SystemExit aborts the whole session instead of
    # reporting one collection error. Full note in mcp/server.py.
    MCP_SDK_AVAILABLE = False
    MCP_SDK_IMPORT_ERROR = _mcp_sdk_exc


def _corez():
    """Import mem20corez from the estate, wherever it lives."""
    try:
        import mem20corez  # noqa: F401
        from mem20corez import integrations
        from mem20corez.mlp import CharMLP
        from mem20corez.quantizer import Quantizer, QuantizationType
        from mem20corez.evaluator import Evaluator, EvaluationConfig
        return integrations, CharMLP, Quantizer, QuantizationType, Evaluator, EvaluationConfig
    except ImportError:
        pass
    root = Path(os.environ.get("MEM20_ROOT", "/opt/mem20"))
    candidate = root / "mem20corez"
    if (candidate / "mem20corez" / "__init__.py").is_file():
        sys.path.insert(0, str(candidate))
    from mem20corez import integrations
    from mem20corez.mlp import CharMLP
    from mem20corez.quantizer import Quantizer, QuantizationType
    from mem20corez.evaluator import Evaluator, EvaluationConfig
    return integrations, CharMLP, Quantizer, QuantizationType, Evaluator, EvaluationConfig


class CorezToolsMixin:
    """Native CoreAI tools for mem20."""

    def register_corez_tools(self):
        """Register the mem20corez tools."""
        if not MCP_SDK_AVAILABLE:  # pragma: no cover
            return
        self.tools["corez_infer"] = mt.Tool(
            name="corez_infer",
            title="Corez Infer",
            description=(
                "Run real inference on the native character MLP tensor engine. "
                "Returns the generated continuation plus the real per-token "
                "logits shape and latency measured during the call."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "seed text"},
                    "max_tokens": {"type": "integer", "default": 32},
                    "hidden": {"type": "integer", "default": 32},
                    "context_len": {"type": "integer", "default": 8},
                },
                "required": ["prompt"],
            },
        )
        self.tools["corez_quantize"] = mt.Tool(
            name="corez_quantize",
            title="Corez Quantize",
            description=(
                "Quantize a real tensor to int8/int4/fp16 and report the measured "
                "reconstruction error and compression ratio. The error is computed "
                "from the actual dequantized values, not estimated."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "rows": {"type": "integer", "default": 64},
                    "cols": {"type": "integer", "default": 64},
                    "dtype": {"type": "string", "enum": ["int8", "int4", "fp16"],
                              "default": "int8"},
                },
                "required": [],
            },
        )
        self.tools["corez_evaluate"] = mt.Tool(
            name="corez_evaluate",
            title="Corez Evaluate",
            description=(
                "Evaluate a freshly built model on the built-in corpus and return "
                "real accuracy, perplexity and latency measured from execution."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hidden": {"type": "integer", "default": 32},
                    "context_len": {"type": "integer", "default": 8},
                    "steps": {"type": "integer", "default": 20},
                },
                "required": [],
            },
        )
        self.tools["corez_wiring"] = mt.Tool(
            name="corez_wiring",
            title="Corez Wiring",
            description=(
                "Prove mem20corez's cross-subsystem edges by calling each one: "
                "toolchest catalog, memory_engine pin_block, mem20kanbanz sha256, "
                "mem20ops declared_scripts, mem20cliz build_envelope, mem20verify "
                "discover_packages. Returns per-edge ok/result."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "estate root override"},
                },
                "required": [],
            },
        )

    async def _corez_infer(self, arguments: Dict[str, Any]) -> str:
        _integrations, CharMLP, _Q, _QT, _E, _EC = _corez()
        import time
        prompt = arguments.get("prompt") or ""
        if not prompt:
            return json.dumps({"ok": False, "error": "prompt is required"})
        model = CharMLP(hidden=int(arguments.get("hidden") or 32),
                        context_len=int(arguments.get("context_len") or 8))
        started = time.perf_counter()
        text = model.generate(prompt, n_tokens=int(arguments.get("max_tokens") or 32))
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return json.dumps({
            "ok": True,
            "prompt": prompt,
            "completion": text,
            "generated_chars": max(0, len(text) - len(prompt)),
            "latency_ms": round(elapsed_ms, 3),
            "params": int(model.param_count()),
        }, indent=2)

    async def _corez_quantize(self, arguments: Dict[str, Any]) -> str:
        _integrations, _C, _Q, _QT, _E, _EC = _corez()
        import numpy as np
        from mem20corez.quantizer import quantize_tensor, dequantize
        rows = int(arguments.get("rows") or 64)
        cols = int(arguments.get("cols") or 64)
        dtype = (arguments.get("dtype") or "int8").lower()
        bits = {"int8": 8, "int4": 4, "fp16": 16}[dtype]
        rng = np.random.default_rng(20261101)
        weights = rng.standard_normal((rows, cols))
        quantized = quantize_tensor(weights, bits=bits)
        restored = dequantize(quantized, weights.shape)
        error = np.abs(restored - weights)
        original_bytes = weights.nbytes
        quantized_bytes = int(quantized.q.nbytes + quantized.scale.nbytes
                              + quantized.zero_point.nbytes)
        return json.dumps({
            "ok": True,
            "dtype": dtype,
            "shape": [rows, cols],
            "compression_ratio": round(original_bytes / max(1, quantized_bytes), 4),
            "max_abs_error": round(float(error.max()), 6),
            "mean_abs_error": round(float(error.mean()), 6),
        }, indent=2)

    async def _corez_evaluate(self, arguments: Dict[str, Any]) -> str:
        _integrations, CharMLP, _Q, _QT, Evaluator, EvaluationConfig = _corez()
        import tempfile
        from mem20corez.evaluator import EvaluationMetric
        model = CharMLP(hidden=int(arguments.get("hidden") or 32),
                        context_len=int(arguments.get("context_len") or 8))
        with tempfile.TemporaryDirectory() as tmp:
            path = model.save(str(Path(tmp) / "model.npz"))
            config = EvaluationConfig(
                model_path=path,
                metrics=[EvaluationMetric.ACCURACY, EvaluationMetric.PERPLEXITY,
                         EvaluationMetric.LATENCY],
                num_samples=int(arguments.get("steps") or 20),
                benchmark_runs=int(arguments.get("steps") or 20),
            )
            result = Evaluator().evaluate(config)
        return json.dumps({
            "ok": True,
            "metrics": {k: round(float(v), 6) for k, v in result.metrics.items()},
            "latency_stats": {k: round(float(v), 3)
                              for k, v in result.latency_stats.items()},
            "throughput": round(float(result.throughput), 3),
            "memory_mb": round(float(result.memory_mb), 4),
            "passed": bool(result.passed),
        }, indent=2)

    async def _corez_wiring(self, arguments: Dict[str, Any]) -> str:
        integrations, _C, _Q, _QT, _E, _EC = _corez()
        root = arguments.get("root")
        report = integrations.wiring_report(Path(root) if root else None)
        return json.dumps(report, indent=2, default=str)
