"""Comic pipeline: parse a shooting script and generate page images."""

import os
import re


IDENTITY_PREFIX = (
    "Comic page, locked visual identity: obsidian #0C0C0C and charcoal blacks, "
    "bone #DED6C4 highlights, acid-green #CCFF00 accents only. Scratchy dry-brush "
    "inking, dense cross-hatching, heavy spotted blacks, newsprint grain, distressed "
    "edges, aged paper. MEM20 COMICS masthead, issue number in ochre, code-authority "
    "footer. Noir, precise, darkly satirical. "
)


class ComicPipeline:
    def __init__(self, adapter_name="openai", out_dir=".", identity_prefix=IDENTITY_PREFIX):
        from .adapters import AdapterRegistry
        self.adapter = AdapterRegistry.get(adapter_name)
        self.out_dir = out_dir
        self.identity_prefix = identity_prefix
        os.makedirs(out_dir, exist_ok=True)

    def parse_beats(self, script_path):
        text = open(script_path, encoding="utf-8").read()
        beats = []
        for line in text.splitlines():
            m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|", line)
            if m and m.group(1).strip().isdigit():
                beats.append({"page": int(m.group(1).strip()), "title": m.group(2).strip(), "beat": m.group(3).strip()})
        return beats

    def run(self, script_path):
        beats = self.parse_beats(script_path)
        results = []
        for b in beats:
            prompt = self.identity_prefix + b["title"] + ". " + b["beat"]
            out = os.path.join(self.out_dir, f"page_{b['page']:02d}.png")
            path = self.adapter.generate(prompt, out)
            results.append({"page": b["page"], "path": path})
        return results