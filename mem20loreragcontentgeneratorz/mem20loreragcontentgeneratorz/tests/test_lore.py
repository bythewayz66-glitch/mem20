import tempfile
import unittest
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from mem20loreragcontentgeneratorz.domain import estate_context, generate, quality_score, retrieve, retrieve_from_memory


class TestLoreRag(unittest.TestCase):
    def test_local_retrieve_and_generate(self):
        docs = [{"text": "dragons live in caves"}, {"text": "elves love forests"}]
        got = retrieve(docs, "dragon caves", k=1)
        self.assertTrue(got)
        out = generate(got, "tell me")
        self.assertIn("tell me", out["output"])

    def test_grounded_retrieval_memory_engine(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = EngineConfig(store_path=Path(d).resolve())
            eng = MemoryEngine(cfg)
            eng.remember("lore", "The ancient dragon guards the crystal cave.", epistemic_status="observed")
            docs = retrieve_from_memory("dragon cave", store_path=d, k=3)
            self.assertTrue(isinstance(docs, list))
            out = generate(docs, "describe the guardian")
            self.assertIn("describe the guardian", out["output"])

    def test_quality_and_estate_context(self):
        self.assertGreaterEqual(quality_score("dragon cave", "dragon cave"), 0.9)
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))


if __name__ == "__main__":
    unittest.main()
