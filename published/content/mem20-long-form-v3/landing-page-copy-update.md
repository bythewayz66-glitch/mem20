# Landing page copy update notes (v3)

Target: the GitHub Pages site. Cite only that public URL in copy.

## Replacements

1. Hero lede: 268 tools across 26 domains becomes 270 tools across 27 domains.
2. All repo links move to the canonical bythewayz66-glitch/mem20 path.
3. Clone URL uses the canonical repo.
4. Install deps use pip install -r requirements.txt instead of the retired SDK pin and editable install.
5. Run command uses the script entry point instead of the retired module path.
6. Install note says the project is not on PyPI and installs from source.
7. Footer count line becomes 270 tools, 27 domains.
8. Benchmark caption adds: self-reported on internal harness, not independently audited.

## Unchanged

Version badge 2.1.0rc2. Benchmark table, no-LoCoMo caveat, adversarial 0.000 row, comparison table, guardrail language. House numbers hold.

## Substantive fixes

Old SDK pin contradicted the tree (mcp>=2.1.1). Old run command named a module from the non-canonical repo.
