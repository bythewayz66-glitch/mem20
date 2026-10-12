# 5000QA — a 5,000-question QA evaluation harness for mem20

## Status: SCAFFOLD — no questions have been executed

**There is no 5000QA specification, dataset, or reference anywhere in this
repository.** That was checked, not assumed: a repo-wide search for `5000QA`,
`5000qa`, `5000_qa` and `5000 questions` across `*.py`, `*.md` and `*.json`
(excluding `node_modules`) returns nothing.

So this is the most reasonable interpretation of the request: a
**5,000-question QA benchmark harness** that drives the real MCP server over
stdio, with a documented question schema, defined scoring, and a results table.

**The results table ships EMPTY.** No score in this directory is a measurement.
Do not quote a 5000QA number until `qa5000.py run` has actually been executed
against a populated question file and the output written to `results.md`.

## Why 5,000 questions

5,000 is a target size, not a magic number. It is large enough that a
per-category accuracy figure has a usable confidence interval: at n=5,000 and
an observed accuracy near 0.5, the 95% interval is roughly ±1.4 points. At
n=500 it is roughly ±4.4 points, which is too wide to distinguish a real
regression from noise.

## Question schema

One JSON object per line (JSONL). See `questions.schema.json` for the formal
schema. Fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Stable unique id, e.g. `q00001` |
| `category` | enum | yes | See categories below |
| `question` | string | yes | The natural-language query sent to the server |
| `expected_answer` | string | yes | The reference answer |
| `evidence_ids` | string[] | no | Record ids that must appear in retrieval |
| `difficulty` | enum | no | `easy` \| `medium` \| `hard` |
| `partition_probe` | bool | no | True if this question tests grounded/simulated separation |
| `expect_refusal` | bool | no | True if the correct behaviour is to refuse or report absence |
| `metadata` | object | no | Free-form provenance (source, author, date) |

### Categories

| Category | What it measures |
|---|---|
| `factual_recall` | Can the server return a fact it was told? |
| `temporal_recall` | Does `recall_at()` resolve the right version at a point in time? |
| `partition_integrity` | Does a simulated record stay out of grounded recall? |
| `epistemic_provenance` | Is `epistemic_status` reported and correct? |
| `multi_hop` | Does retrieval compose two or more facts? |
| `negative_control` | Does the server correctly report *absence* rather than confabulate? |

`negative_control` is the most important category. A memory system that answers
every question is not accurate, it is agreeable. These questions have no answer
in the store, and the correct behaviour is to say so.

## Scoring

Per question, three independent signals:

1. **Answer score** — token-level F1 against `expected_answer`, plus exact-match
   after normalisation. F1 is the headline; exact match is reported alongside.
2. **Evidence hit rate** — fraction of `evidence_ids` present in the retrieved
   set. Only computed when `evidence_ids` is non-empty.
3. **Refusal correctness** — for `expect_refusal` questions, 1.0 if the server
   reported absence and 0.0 if it produced an answer. For all other questions,
   1.0 if it produced an answer and 0.0 if it refused.

A question is **correct** when its answer score is at or above the threshold
(default 0.5) and its refusal behaviour is correct. Aggregate accuracy is
reported per category and overall, with the count of scored questions so a
partial run cannot be mistaken for a full one.

## Running

```bash
# 1. Generate questions from a live store (derives them from real facts).
python3 bench/qa5000/qa5000.py generate \
    --store /path/to/store --out bench/qa5000/questions.jsonl --target 5000

# 2. Run them against the MCP server over stdio.
python3 bench/qa5000/qa5000.py run \
    --questions bench/qa5000/questions.jsonl \
    --server mcp/mcp_server.py \
    --out bench/qa5000/results.md

# 3. Inspect the per-category breakdown.
python3 bench/qa5000/qa5000.py report --results bench/qa5000/results.md
```

## Honest limitations

- **The 5,000 questions are a scaffold, not a dataset.** `generate` derives
  questions from whatever is in the store it is pointed at. A store with 200
  facts cannot yield 5,000 non-duplicate questions, and the generator will say
  so rather than pad the file with paraphrases.
- **No questions have been executed.** The results table is empty by design.
- **Answer scoring is lexical, not semantic.** Token F1 will under-credit a
  correct answer phrased differently. Treat it as a lower bound and read the
  per-category breakdown rather than the single headline number.
- **The harness drives the server over stdio**, so it measures the real tool
  surface including the partition guards — not an in-process import.
