"""The models proven to answer on this host, recorded so the roster cannot drift.

Generated from a live probe. Kept as data rather than re-probed in CI, because
the point of the roster test is to catch *edits to the roster* that introduce an
unverified model - not to re-bill providers on every test run.

2026-11-11: keyless-only. All three ids below answered a real completion on
this host with no API key: gpt-oss-20b through the pollinations proxy (~5s),
qwen2.5-coder:0.5b and gemma3:1b through local Ollama
(http://localhost:11434/v1).
"""

VERIFIED = {
    # pollinations (keyless remote proxy)
    "gpt-oss-20b",
    # ollama (local, keyless)
    "qwen2.5-coder:0.5b",
    "gemma3:1b",
}
