"""Context compression forge: summarize, compress, retain key info."""
import math, hashlib


def compress(text, ratio=0.5):
    words = text.split()
    keep = max(1, int(len(words) * ratio))
    # keep first + last + sampled
    if keep >= len(words):
        return text
    head = words[:keep // 2]
    tail = words[-(keep - len(head)):]
    return " ".join(head + ["..."] + tail)


def extractive_summary(text, n_sentences=3):
    sents = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sents) <= n_sentences:
        return sents
    # score by length + position
    scored = sorted(enumerate(sents), key=lambda x: -len(x[1]))[:n_sentences]
    scored.sort(key=lambda x: x[0])
    return [s for _, s in scored]


def compression_ratio(original, compressed):
    if not original:
        return 0.0
    return round(len(compressed) / len(original), 4)


def key_terms(text, top=5):
    words = [w.lower().strip(".,!?") for w in text.split()]
    from collections import Counter
    c = Counter(w for w in words if len(w) > 3)
    return [w for w, _ in c.most_common(top)]


def forge_context(chunks, max_tokens=1000):
    out = []
    used = 0
    for ch in chunks:
        if used + len(ch) > max_tokens:
            break
        out.append(ch)
        used += len(ch)
    return {"chunks": out, "used_tokens": used, "remaining": max_tokens - used}
