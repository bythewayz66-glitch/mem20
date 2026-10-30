"""Runtime prompt optimizer: optimize prompts for cost/quality."""
import re


def tokenize(prompt):
    return prompt.split()


def compress(prompt, max_tokens=100):
    toks = tokenize(prompt)
    if len(toks) <= max_tokens:
        return prompt
    return " ".join(toks[:max_tokens]) + "..."


def score_prompt(prompt, metrics):
    # metrics: dict of keyword->weight
    score = 0.0
    for k, w in metrics.items():
        if k.lower() in prompt.lower():
            score += w
    return round(score, 4)


def optimize(prompt, metrics, max_tokens=100):
    compressed = compress(prompt, max_tokens)
    return {"prompt": compressed, "score": score_prompt(compressed, metrics), "tokens": len(tokenize(compressed))}


def prompt_health(prompts):
    return {"count": len(prompts), "avg_tokens": round(sum(len(tokenize(p)) for p in prompts)/max(1,len(prompts)),2)}
