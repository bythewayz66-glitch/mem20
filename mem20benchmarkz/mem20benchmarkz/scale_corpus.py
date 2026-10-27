"""Deterministic scale corpus v2 for mem20benchmarkz.

`mem20-scale-corpus-v2` — 2,000 records across three labelled categories, plus
250 probes. Same seed always yields the same bytes, so the corpus is
reproducible and the JSONL is a build artifact, not a checked-in blob.

    mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
    mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --out benchmarks/results

## What changed from v1, and why

v1 generated 2,000 records of the form
`[s0001] deploy record 00001: build 4500 on runner-02; policy tag P3; note
checksum 1a2b3c` — synthetic strings with no referent — and 20 queries of the
form `is Zephyra sector 3 a real prod mem20 node`, with `supports=()` and
`expect=()`. An answer-free query cannot be answered, so its hit rate was 0.000
by construction; `bench.run()` then hardcoded the same verdict, so the two
errors reinforced each other and the published 0.000 looked like a retrieval
result. It was not. It was arithmetic.

v2 fixes both halves:

1. **Every answerable probe has its gold record in the corpus, and the answer
   token is absent from the probe text.** `validate()` enforces this pair of
   conditions mechanically for every non-control query, so an answer-free
   adversarial probe cannot be generated again by accident.
2. **Adversarial probes are harder than a lookup, not impossible.** They ask for
   the same fact as a direct probe but (a) supply a *different designator* for
   the subject (symbol instead of name, alpha-2 instead of name) and (b) replace
   the relation label with a synonym, so lexical matching cannot lean on the
   record's own wording. `adversarial` keeps a partial lexical anchor;
   `adversarial_hard` removes the relation words entirely.
3. **A control row survives.** `unanswerable` probes name a fictional subject
   and nothing in the corpus can answer them. They score 0.000 always, and they
   are the check that the metric is not handing out free hits. They are a
   separate kind from `adversarial` so the two can never be confused again.

## Categories

Records are labelled `grounded`, `ungrounded` or `false`, at a documented
1/3-ish split. Grounded and false share real reference data (periodic table,
ISO-3166, mime-db) cached under `reference/v2/`; ungrounded invents a coherent
but unsourced universe. A `false` record is a deterministic mutation of a real
grounded record and carries `contradicts` (the grounded key) plus `true_value`.
That mutation is what makes `contradiction` probes answerable: the store holds
the truth the lie denies.

Grounded facts are genuinely checkable — each carries a `source` URL and the
verbatim `evidence` string the fact was transcribed from. False facts are
demonstrably wrong against that same evidence. The categories are not blurred:
a record is in exactly one of them, and the validator refuses a `grounded`
record without a source or a `false` record without a `contradicts` target.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .corpus import Corpus, Fact, Query

SCALE_NAME = "mem20-scale-corpus-v2"
SCALE_SEED = 20261027

# Totals. `SCALE_RECORDS` is the whole corpus; the split is deliberate and
# stated here so the manifest and the report cannot drift apart.
SCALE_RECORDS = 2000
SCALE_GROUNDED = 700
SCALE_UNGROUNDED = 650
SCALE_FALSE = 650

# Probe counts per kind.
SCALE_DIRECT = 60
SCALE_MULTI = 30
SCALE_ADVERSARIAL = 60
SCALE_ADVERSARIAL_HARD = 40
SCALE_CONTRADICTION = 40
SCALE_UNANSWERABLE = 20

REFERENCE_DIR = Path(__file__).resolve().parent.parent.parent / "reference" / "v2"

SOURCES = {
    "element": ("https://raw.githubusercontent.com/Bowserinator/"
                "Periodic-Table-JSON/master/PeriodicTableJSON.json"),
    "country": ("https://raw.githubusercontent.com/lukes/"
                "ISO-3166-Countries-with-Regional-Codes/master/all/all.json"),
    "mime": "https://raw.githubusercontent.com/jshttp/mime-db/master/db.json",
}


@dataclass(frozen=True)
class Seed:
    """One generated fact plus the designators a paraphrase probe may use."""

    family: str
    key: str
    content: str
    evidence: str
    subject: str
    predicate: str
    obj: str
    # The literal substring of `content` that proves the answer. Probes expect
    # this exact phrase, so the validator can check it really is in the record.
    # Keeping it explicit (rather than gluing predicate+object together) is what
    # stops a probe from demanding text the corpus never wrote.
    gold_phrase: str = ""
    # For a false record: the value the claim asserts (wrong) and the value it
    # contradicts (true). `obj` is always the value the RECORD asserts, so a
    # false record's `object` must be the wrong one — publishing the true value
    # in an `object` field labelled `false` would be a metadata lie.
    true_value: str = ""
    # Alternative designators for the same subject, for paraphrase probes.
    aliases: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# reference data
# --------------------------------------------------------------------------

def _load_json(name: str):
    path = REFERENCE_DIR / name
    if not path.is_file():
        raise FileNotFoundError(
            f"missing cached reference data at {path}.\n"
            "The corpus is generated offline from a cache so a re-run does not "
            "depend on the network. Fetch it once with:\n"
            f"  mkdir -p {REFERENCE_DIR} && \\\n"
            f"  curl -sL -o {REFERENCE_DIR / 'periodic-table.json'} {SOURCES['element']} && \\\n"
            f"  curl -sL -o {REFERENCE_DIR / 'iso-3166.json'} {SOURCES['country']} && \\\n"
            f"  curl -sL -o {REFERENCE_DIR / 'mime-db.json'} {SOURCES['mime']}")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _slug(text: str) -> str:
    out = []
    for ch in text.lower():
        out.append(ch if ch.isalnum() else "-")
    return "".join(out).strip("-")[:48] or "x"


def grounded_seeds() -> list[Seed]:
    """Round-robin over three real sources so no family dominates the corpus.

    Ordering matters: iterating one family to exhaustion first would fill every
    grounded slot with elements and make the corpus a single-domain toy.
    """
    elements = _load_json("periodic-table.json")["elements"]
    countries = _load_json("iso-3166.json")
    mimes = _load_json("mime-db.json")

    per_element: list[Seed] = []
    for e in elements:
        name, symbol = e.get("name"), e.get("symbol")
        number = e.get("number")
        mass = e.get("atomic_mass")
        phase = e.get("phase")
        if not (name and symbol and isinstance(number, int) and mass):
            continue
        mass_s = f"{float(mass):.3f}".rstrip("0").rstrip(".")
        content = (f"Chemical element {symbol} ({name}) has atomic number "
                   f"{number} and standard atomic weight {mass_s}"
                   + (f"; its phase at standard conditions is {phase}." if phase else "."))
        evidence = (f"{name} ({symbol}) number={number} "
                    f"atomic_mass={mass} phase={phase}")
        per_element.append(Seed(
            family="element",
            key=f"el-{_slug(name)}-{number}",
            content=content,
            evidence=evidence,
            subject=name,
            predicate="has atomic number",
            obj=str(number),
            gold_phrase=f"atomic number {number}",
            aliases=(symbol,),
        ))

    per_country: list[Seed] = []
    for c in countries:
        name, a2, region = c.get("name"), c.get("alpha-2"), c.get("region")
        if not (name and a2 and region):
            continue
        sub = c.get("sub-region")
        content = (f"The country {name} is assigned the two-letter code {a2} "
                   f"and belongs to the region {region}"
                   + (f" (sub-region {sub})." if sub else "."))
        evidence = f"{name} alpha-2={a2} region={region} sub-region={sub}"
        per_country.append(Seed(
            family="country",
            key=f"co-{_slug(name)}-{a2.lower()}",
            content=content,
            evidence=evidence,
            subject=name,
            predicate="has two-letter code",
            obj=a2,
            gold_phrase=f"two-letter code {a2}",
            aliases=(a2,),
        ))

    per_mime: list[Seed] = []
    for mtype, meta in sorted(mimes.items()):
        if "/" not in mtype:
            continue
        charset = meta.get("charset")
        compressible = meta.get("compressible")
        if charset is None and compressible is None:
            continue
        bits = []
        if charset:
            bits.append(f"declares charset {charset}")
        if compressible is not None:
            bits.append("is marked compressible" if compressible
                        else "is marked non-compressible")
        content = f"The media type {mtype} " + " and ".join(bits) + "."
        evidence = (f"mime-db {mtype}: charset={charset} "
                    f"compressible={compressible}")
        obj = charset or ("compressible" if compressible else "non-compressible")
        gold_phrase = (f"declares charset {charset}" if charset else
                       ("marked compressible" if compressible
                        else "marked non-compressible"))
        per_mime.append(Seed(
            family="mime",
            key=f"mi-{_slug(mtype)}",
            content=content,
            evidence=evidence,
            subject=mtype,
            predicate="declares charset" if charset else "is compressible",
            obj=str(obj),
            gold_phrase=gold_phrase,
            aliases=(),
        ))

    families = (per_element, per_country, per_mime)
    out: list[Seed] = []
    seen: set[str] = set()
    i = 0
    while len(out) < SCALE_GROUNDED and any(i < len(f) for f in families):
        for fam in families:
            if i < len(fam):
                seed = fam[i]
                if seed.key not in seen:
                    seen.add(seed.key)
                    out.append(seed)
        i += 1
        if i > 5000:  # defensive: never spin
            break
    return out[:SCALE_GROUNDED]


# --------------------------------------------------------------------------
# ungrounded universe (fictional, internally consistent, no source)
# --------------------------------------------------------------------------

_ORG_WORDS = ("Halden", "Tessaly", "Orvyx", "Calder", "Nimbari", "Quillon",
              "Vasterly", "Merrow", "Dravent", "Solvane", "Pellow", "Skarn",
              "Aurelis", "Brantwell", "Corvani", "Illworth")
_ORG_KIND = ("Logistics", "Labs", "Foundry", "Analytics", "Systems",
             "Dynamics", "Works", "Collective")
_CITY_WORDS = ("Alderhow", "Brackmoor", "Cassavale", "Dunmarch", "Elderfen",
               "Fallcrest", "Glimmervik", "Harrowgate", "Ivymount", "Jessup",
               "Kaldrast", "Lowmarsh", "Mirrhaven", "Northgate", "Oakspire")
_ROLE = ("chief archivist", "head of retrieval", "reliability lead",
         "platform steward", "data custodian")


def _pick(pool: tuple[str, ...], n: int) -> str:
    return pool[n % len(pool)]


def ungrounded_seeds() -> list[Seed]:
    """A coherent but entirely invented universe — no source, by design."""
    out: list[Seed] = []
    for i in range(SCALE_UNGROUNDED):
        org = f"{_pick(_ORG_WORDS, i)} {_pick(_ORG_KIND, i * 3)}"
        city = _pick(_CITY_WORDS, i * 7)
        role = _pick(_ROLE, i * 5)
        if i % 3 == 0:
            badge = 1000 + i
            content = (f"{org} operates a retrieval cluster in {city} under "
                       f"internal badge R-{badge}, reporting to the {role}.")
            pred, obj = "operates cluster under badge", f"R-{badge}"
            gold = f"badge R-{badge}"
        elif i % 3 == 1:
            head = 4 + (i % 40)
            content = (f"{org} splits its {city} workload across {head} shards "
                       f"and reviews shard balance every {6 + (i % 5)} weeks.")
            pred, obj = "splits workload across shards", str(head)
            gold = f"across {head} shards"
        else:
            ver = f"{2 + (i % 9)}.{i % 7}.{i % 5}"
            content = (f"{org} pins the {city} ingestion pipeline at release "
                       f"{ver} and freezes schema changes during audits.")
            pred, obj = "pins ingestion pipeline at", ver
            gold = f"release {ver}"
        out.append(Seed(
            family="fiction",
            key=f"ug-{i:04d}",
            content=content,
            evidence="",
            subject=org,
            predicate=pred,
            obj=obj,
            gold_phrase=gold,
            aliases=(city,),
        ))
    return out


# --------------------------------------------------------------------------
# false records: deterministic mutations of real facts
# --------------------------------------------------------------------------

def _mutate_number(value: str) -> str:
    """Shift an integer so the result cannot equal the truth."""
    try:
        n = int(value)
    except ValueError:
        return value + "0"
    return str(n + 1 if n % 2 == 0 else n - 1)


def false_seeds(grounded: list[Seed]) -> list[Seed]:
    """Wrong claims about real entities, each pointing at the true record.

    The mutation is chosen per family so the result stays *plausible* — a wrong
    atomic number, a code belonging to another country, a charset the type does
    not declare — rather than a randomly scrambled sentence.
    """
    out: list[Seed] = []
    by_family: dict[str, list[Seed]] = {}
    for g in grounded:
        by_family.setdefault(g.family, []).append(g)

    for i in range(SCALE_FALSE):
        family = ("element", "country", "mime")[i % 3]
        pool = by_family.get(family) or grounded
        true = pool[i % len(pool)]
        other = pool[(i * 7 + 3) % len(pool)]

        if family == "element" and true is not other:
            wrong = _mutate_number(true.obj)
            content = (f"Chemical element {true.subject} has atomic number "
                       f"{wrong}; this was reassigned in the 2019 revision.")
            wrong_obj = wrong
        elif family == "country" and other.obj != true.obj:
            content = (f"The country {true.subject} is assigned the two-letter "
                       f"code {other.obj} in the current ISO register.")
            wrong_obj = other.obj
        elif family == "mime":
            wrong_charset = "utf-16" if "utf-8" in (true.obj or "") else "utf-8"
            content = (f"The media type {true.subject} declares charset "
                       f"{wrong_charset} in the published registry.")
            wrong_obj = wrong_charset
        else:
            content = (f"The record {true.subject} was superseded and now "
                       f"carries no registered value.")
            wrong_obj = "none"

        out.append(Seed(
            family=f"false-{family}",
            key=f"fa-{i:04d}",
            content=content,
            evidence="",
            subject=true.subject,
            predicate=true.predicate,
            obj=wrong_obj,
            gold_phrase=true.gold_phrase,
            true_value=true.obj,
            aliases=(true.key,),
        ))
    return out


# --------------------------------------------------------------------------
# queries
# --------------------------------------------------------------------------

# Relation-label synonyms: the hard paraphraser swaps the record's own wording
# for a different one so BM25 cannot match on it.
_SYNONYM = {
    "has atomic number": "occupies which position in the periodic sequence",
    "has two-letter code": "carries which designation in the ISO register",
    "declares charset": "registers which character encoding",
    "is compressible": "is flagged as which compression class",
}


def _hard_relation(predicate: str) -> str:
    return _SYNONYM.get(predicate, "is documented as which value")


def build_queries(grounded: list[Seed], false: list[Seed]) -> list[Query]:
    """Probes whose answers all exist in the corpus, plus a 0.000 control."""
    queries: list[Query] = []

    # -- direct: subject named, relation named, answer required --------------
    for i in range(SCALE_DIRECT):
        g = grounded[i % len(grounded)]
        alias = g.aliases[0] if g.aliases else g.subject
        if g.family == "element":
            text = f"what atomic number does {alias} have"
        elif g.family == "country":
            text = f"what two-letter code is {alias} assigned"
        else:
            text = f"what charset does {alias} declare"
        queries.append(Query(
            qid=f"d{i:03d}", text=text, kind="direct",
            supports=(g.key,), expect=(g.gold_phrase,),
            gold_key=g.key, difficulty="easy"))

    # -- adversarial: different designator, answer token absent --------------
    # Probes index into `alias_pool` — records that carry a second designator
    # (element symbol, country alpha-2). Indexing the full pool instead and
    # skipping misses would silently under-fill this class, which is exactly the
    # kind of thin adversarial sample that produced the original 3-query 0.000.
    alias_pool = [g for g in grounded if g.aliases]
    for i in range(SCALE_ADVERSARIAL):
        g = alias_pool[(i * 11 + 5) % len(alias_pool)]
        designator = g.aliases[0]
        text = (f"what does the register say the designation {designator} "
                f"is recorded as")
        queries.append(Query(
            qid=f"a{i:03d}", text=text, kind="adversarial",
            supports=(g.key,), expect=(g.gold_phrase,),
            gold_key=g.key, difficulty="hard"))

    # -- adversarial_hard: synonym relation, no lexical overlap on the label -
    for i in range(SCALE_ADVERSARIAL_HARD):
        g = alias_pool[(i * 17 + 9) % len(alias_pool)]
        designator = g.aliases[0]
        text = (f"for the designation {designator}, which registered value "
                f"applies")
        queries.append(Query(
            qid=f"h{i:03d}", text=text, kind="adversarial_hard",
            supports=(g.key,), expect=(g.gold_phrase,),
            gold_key=g.key, difficulty="hard"))

    # -- contradiction: the false claim, asked for the correction ------------
    by_key = {g.key: g for g in grounded}
    for i in range(SCALE_CONTRADICTION):
        f = false[(i * 3) % len(false)]
        target = by_key.get(f.aliases[0])
        if target is None:
            continue
        claim = f.content.split(";")[0].rstrip(".")
        queries.append(Query(
            qid=f"c{i:03d}", text=f"correct this claim: {claim}",
            kind="contradiction", supports=(target.key,),
            expect=(target.gold_phrase,),
            gold_key=target.key, difficulty="hard"))

    # -- multi_hop: one entity, grounded record plus its neighbours ----------
    for i in range(SCALE_MULTI):
        g = grounded[(i * 23) % len(grounded)]
        queries.append(Query(
            qid=f"m{i:03d}",
            text=f"what is recorded about {g.subject} in the register",
            kind="multi_hop", supports=(g.key,),
            expect=(g.gold_phrase,), hops=2,
            entity=g.subject, gold_key=g.key, difficulty="medium"))

    # -- unanswerable CONTROL ------------------------------------------------
    # Nothing in the corpus mentions these subjects. 0.000 is the only correct
    # score; anything else means the metric is scoring noise as a hit.
    for i in range(SCALE_UNANSWERABLE):
        city = _pick(_CITY_WORDS, i * 11)
        queries.append(Query(
            qid=f"u{i:03d}",
            text=(f"which internal badge does the Zephyra outpost at {city} "
                  f"operate under"),
            kind="unanswerable", supports=(), expect=(),
            difficulty="control"))

    return queries


# --------------------------------------------------------------------------
# assembly + validation
# --------------------------------------------------------------------------

def build_scale_corpus(n_facts: int | None = None) -> Corpus:
    """Build the full corpus in memory.

    `n_facts` caps the number of *grounded* records so a smoke run can be cheap;
    it exists for CLI compatibility with v1.
    """
    grounded = grounded_seeds()
    if n_facts and n_facts < len(grounded):
        grounded = grounded[:n_facts]
    ungrounded = ungrounded_seeds()
    false = false_seeds(grounded)

    facts = [
        Fact(topic=f"bench.{g.family}", content=g.content,
             tags=(g.family, "grounded"), category="grounded", key=g.key,
             subject=g.subject, predicate=g.predicate, object=g.obj,
             source=SOURCES.get(g.family), evidence=g.evidence, confidence=1.0)
        for g in grounded
    ]
    simulated = [
        Fact(topic=f"bench.{u.family}", content=u.content,
             tags=(u.family, "ungrounded"), category="ungrounded", key=u.key,
             subject=u.subject, predicate=u.predicate, object=u.obj,
             source=None, confidence=0.4)
        for u in ungrounded
    ] + [
        Fact(topic=f"bench.{f.family}", content=f.content,
             tags=(f.family, "false"), category="false", key=f.key,
             subject=f.subject, predicate=f.predicate, object=f.obj,
             source=None, contradicts=f.aliases[0], true_value=f.true_value,
             confidence=0.2)
        for f in false
    ]
    return Corpus(
        name=SCALE_NAME,
        facts=facts,
        simulated=simulated,
        queries=build_queries(grounded, false),
    )


def validate(corpus: Corpus) -> dict:
    """Machine-check the two invariants the old corpus violated.

    * every non-control probe's gold record exists in the corpus, and the gold
      answer text actually appears in that record's content;
    * the answer text does NOT appear in the probe, so the probe is a real
      retrieval task and not a lookup of its own words.

    Also checks category labels, source/contradicts rules, and duplicate keys.
    """
    errors: list[str] = []
    all_records = corpus.facts + corpus.simulated
    keys = [f.key for f in all_records]
    if len(keys) != len(set(keys)):
        errors.append(f"duplicate keys: {len(keys) - len(set(keys))}")
    if any(k is None for k in keys):
        errors.append("records with a null key")

    by_key = {f.key: f for f in all_records}
    for f in all_records:
        if f.category == "grounded" and not f.source:
            errors.append(f"grounded record {f.key} has no source")
        if f.category == "false" and not f.contradicts:
            errors.append(f"false record {f.key} has no contradicts target")
        if f.category not in ("grounded", "ungrounded", "false"):
            errors.append(f"record {f.key} has category {f.category!r}")

    checked = 0
    for q in corpus.queries:
        if q.kind == "unanswerable":
            if q.expect or q.supports:
                errors.append(f"{q.qid}: control probe must not expect evidence")
            continue
        if not q.expect:
            errors.append(f"{q.qid}: answerable probe has no expected evidence")
            continue
        gold = by_key.get(q.gold_key or "")
        if gold is None:
            errors.append(f"{q.qid}: gold record {q.gold_key!r} not in corpus")
            continue
        needle = q.expect[0].lower()
        if needle not in gold.content.lower():
            errors.append(
                f"{q.qid}: expected evidence {needle!r} absent from gold "
                f"record {q.gold_key!r} — the answer is not in the corpus")
            continue
        if needle in q.text.lower():
            errors.append(
                f"{q.qid}: expected evidence {needle!r} appears in the probe "
                f"text — the probe leaks its own answer")
            continue
        checked += 1

    return {
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors[:50],
        "answerable_probes_checked": checked,
        "total_probes": len(corpus.queries),
        "records": len(all_records),
        "by_category": _counts(corpus),
    }


def _counts(corpus: Corpus) -> dict:
    out: dict[str, int] = {}
    for f in corpus.facts + corpus.simulated:
        out[f.category] = out.get(f.category, 0) + 1
    return out


# --------------------------------------------------------------------------
# disk form
# --------------------------------------------------------------------------

def _row_fact(f: Fact, prefix: str, i: int) -> dict:
    return {
        "id": f"{prefix}{i:05d}",
        "key": f.key,
        "category": f.category,
        "topic": f.topic,
        "content": f.content,
        "tags": list(f.tags),
        "epistemic_status": f.epistemic_status,
        "subject": f.subject,
        "predicate": f.predicate,
        "object": f.object,
        "confidence": f.confidence,
        "source": f.source,
        "evidence": f.evidence,
        "contradicts": f.contradicts,
        "true_value": f.true_value,
    }


def write_scale_corpus(out_dir: str | Path, n_facts: int | None = None) -> Path:
    """Write records.jsonl, grounded.jsonl, simulated.jsonl, queries.jsonl, manifest."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    corpus = build_scale_corpus(n_facts=n_facts)
    report = validate(corpus)

    def dump(name: str, rows: list[dict]) -> None:
        with (out / name).open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        with (out / name).open(encoding="utf-8") as fh:
            n_lines = sum(1 for ln in fh if ln.strip())
        if n_lines != len(rows):
            raise AssertionError(f"{name}: wrote {len(rows)} rows, read {n_lines}")

    g_rows = [_row_fact(f, "g", i) for i, f in enumerate(corpus.facts)]
    s_rows = [_row_fact(f, "s", i) for i, f in enumerate(corpus.simulated)]
    q_rows = [{
        "qid": q.qid, "text": q.text, "kind": q.kind,
        "expect": list(q.expect), "supports": list(q.supports),
        "hops": q.hops, "entity": q.entity,
        "difficulty": q.difficulty, "gold_key": q.gold_key,
    } for q in corpus.queries]

    dump("grounded.jsonl", g_rows)
    dump("simulated.jsonl", s_rows)
    dump("records.jsonl", g_rows + s_rows)
    dump("queries.jsonl", q_rows)

    kinds: dict[str, int] = {}
    for q in corpus.queries:
        kinds[q.kind] = kinds.get(q.kind, 0) + 1

    manifest = {
        "name": SCALE_NAME,
        "seed": SCALE_SEED,
        "records": len(g_rows) + len(s_rows),
        "grounded": len(g_rows),
        "simulated": len(s_rows),
        "by_category": report["by_category"],
        "queries": len(q_rows),
        "query_kinds": kinds,
        "sources": SOURCES,
        "validation": {
            "status": report["status"],
            "error_count": report["error_count"],
            "answerable_probes_checked": report["answerable_probes_checked"],
        },
        "description": (
            "Scale corpus v2. Every non-control probe has its gold record in the "
            "corpus and does not leak its own answer; the `unanswerable` kind is "
            "a control that must score 0.000. Contamination must stay 0.0."
        ),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                       encoding="utf-8")
    (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    return out


def load_jsonl_corpus(corpus_dir: str | Path) -> Corpus:
    """Load a directory written by write_scale_corpus (or a v2-compatible one)."""
    d = Path(corpus_dir)
    facts: list[Fact] = []
    simulated: list[Fact] = []

    def row_to_fact(row: dict) -> Fact:
        return Fact(
            topic=row["topic"],
            content=row["content"],
            tags=tuple(row.get("tags") or ()),
            epistemic_status=row.get("epistemic_status") or "observed",
            category=row.get("category") or "grounded",
            key=row.get("key"),
            subject=row.get("subject"),
            predicate=row.get("predicate"),
            object=row.get("object"),
            source=row.get("source"),
            evidence=row.get("evidence"),
            contradicts=row.get("contradicts"),
            true_value=row.get("true_value"),
            confidence=float(row.get("confidence") or 1.0),
        )

    for name, sink in (("grounded.jsonl", facts), ("simulated.jsonl", simulated)):
        path = d / name
        if not path.is_file():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    sink.append(row_to_fact(json.loads(line)))

    queries: list[Query] = []
    with (d / "queries.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            queries.append(Query(
                qid=row["qid"], text=row["text"], kind=row["kind"],
                supports=tuple(row.get("supports") or ()),
                expect=tuple(row.get("expect") or ()),
                hops=int(row.get("hops") or 1),
                entity=row.get("entity"),
                difficulty=row.get("difficulty") or "medium",
                gold_key=row.get("gold_key"),
            ))

    name = SCALE_NAME
    man = d / "manifest.json"
    if man.is_file():
        name = json.loads(man.read_text(encoding="utf-8")).get("name", name)
    return Corpus(name=name, facts=facts, queries=queries, simulated=simulated)
