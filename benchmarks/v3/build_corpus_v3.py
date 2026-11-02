#!/usr/bin/env python3
"""mem20-scale-corpus-v3 — deterministic ~100 MB load-test corpus for mem20.

Three labelled categories, one third each:

  grounded    verifiably true, anchored to a real cached source. Carries
              ``source`` (the URL the value was transcribed from) and
              ``evidence`` (the verbatim field values from that source).
  ungrounded  plausible and internally consistent, but invented. No source.
  false       demonstrably wrong: a deterministic mutation of a grounded
              record. Carries ``contradicts`` (the grounded key it denies) and
              ``true_value`` (the value that key actually holds).

The categories are never blurred. A record is in exactly one of them, and the
validator refuses a grounded record without a source or a false record without
a contradicts target.

Determinism: every record is built from ``random.Random(SEED ^ crc32(key))``,
so a re-run at the same seed reproduces the same bytes. Reference data is read
from a local cache under ``reference/v3/`` — generation never touches the
network.

    python benchmarks/v3/build_corpus_v3.py --per-category 30000 \
        --out benchmarks/corpora/v3

Reference sources (fetched once, cached, hashed into the manifest):

  element  https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json
  country  https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json
  mime     https://raw.githubusercontent.com/jshttp/mime-db/master/db.json
  city     https://download.geonames.org/export/dump/cities15000.zip
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import zlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = REPO_ROOT / "reference" / "v3"

SCHEMA_VERSION = "mem20-bench-v3"
CORPUS_NAME = "mem20-scale-corpus-v3"
SEED = 20261101
RETRIEVED = "2026-11-01"

# Fixed base instant for per-record timestamps, so a re-run cannot change bytes.
BASE_TS = datetime(2026, 1, 1, tzinfo=timezone.utc)

SOURCES = {
    "element": ("https://raw.githubusercontent.com/Bowserinator/"
                "Periodic-Table-JSON/master/PeriodicTableJSON.json"),
    "country": ("https://raw.githubusercontent.com/lukes/"
                "ISO-3166-Countries-with-Regional-Codes/master/all/all.json"),
    "mime": "https://raw.githubusercontent.com/jshttp/mime-db/master/db.json",
    "city": "https://download.geonames.org/export/dump/cities15000.zip",
    "codepoint": "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt",
    "countrymeta": ("https://raw.githubusercontent.com/mledoze/"
                    "countries/master/countries.json"),
}

# epistemic_status is mem20's own vocabulary (memory_engine/memory.py).
EPISTEMIC = {
    "grounded": "observed",
    "ungrounded": "imagined",
    "false": "agent_generated",
}

# Share of the grounded pool each family may take. City has 34k rows and would
# otherwise swallow the whole category; the cap keeps the corpus multi-domain.
FAMILY_CAP = {"element": 0.12, "country": 0.10, "mime": 0.14,
              "city": 0.24, "codepoint": 0.28, "countrymeta": 0.12}


@dataclass(frozen=True)
class Seed:
    """One fact, plus everything needed to mutate it into a false claim."""

    family: str
    key: str
    subject: str
    predicate: str
    obj: str
    template: str          # str.format(obj=...) -> the claim text
    evidence: str
    source: str | None
    context: str = ""      # a second, still-true sentence of surrounding detail
    dossier: str = ""      # the entity's full true record, as a memory note
    difficulty: str = "easy"
    aliases: tuple[str, ...] = ()
    gold_phrase: str = ""  # literal substring of content that proves the answer
    true_value: str = ""   # false records only: the value the truth holds


def _slug(text: str) -> str:
    out = []
    for ch in text.lower():
        out.append(ch if ch.isalnum() else "-")
    return "".join(out).strip("-")[:56] or "x"


def _rng(key: str) -> random.Random:
    return random.Random(SEED ^ zlib.crc32(key.encode("utf-8")))


def _ts(key: str) -> str:
    """Deterministic timestamp spread over 2026, derived from the key."""
    offset = zlib.crc32(key.encode("utf-8")) % (365 * 24 * 60)
    return (BASE_TS + timedelta(minutes=offset)).isoformat().replace("+00:00", "Z")


def _num(value, places: int) -> str:
    return f"{float(value):.{places}f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# reference data
# ---------------------------------------------------------------------------

def _load_json(name: str):
    path = REFERENCE_DIR / name
    if not path.is_file():
        raise FileNotFoundError(
            f"missing cached reference data at {path}\n"
            "Fetch it once (see reference/v3/README.md).")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_cities() -> list[list[str]]:
    path = REFERENCE_DIR / "cities15000.txt"
    if not path.is_file():
        raise FileNotFoundError(
            f"missing {path}; unzip cities15000.zip into {REFERENCE_DIR}")
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 18:
                rows.append(parts)
    return rows


# ---------------------------------------------------------------------------
# grounded families
# ---------------------------------------------------------------------------

def _element_seeds() -> list[Seed]:
    elements = _load_json("periodic-table.json")["elements"]
    out: list[Seed] = []
    for e in elements:
        name, symbol = e.get("name"), e.get("symbol")
        number = e.get("number")
        if not (name and symbol and isinstance(number, int)):
            continue
        base = f"el-{_slug(name)}-{number}"
        src = SOURCES["element"]
        period, group = e.get("period"), e.get("group")
        where = (f"It sits in period {period} and group {group} of the periodic "
                 f"table." if period and group else "")

        out.append(Seed(
            family="element", key=f"{base}-z", subject=name,
            predicate="has atomic number", obj=str(number),
            template=f"Chemical element {name} ({symbol}) has atomic number {{obj}}.",
            evidence=f"PeriodicTableJSON: name={name} symbol={symbol} number={number}",
            source=src, context=where, difficulty="easy", aliases=(symbol,),
            gold_phrase=f"atomic number {number}"))

        mass = e.get("atomic_mass")
        if mass:
            mass_s = _num(mass, 3)
            out.append(Seed(
                family="element", key=f"{base}-m", subject=name,
                predicate="has standard atomic weight", obj=mass_s,
                template=(f"The standard atomic weight of {name} ({symbol}) "
                          f"is {{obj}} u."),
                evidence=f"PeriodicTableJSON: name={name} atomic_mass={mass}",
                source=src, context=where, difficulty="medium", aliases=(symbol,),
                gold_phrase=f"is {mass_s} u"))

        phase = e.get("phase")
        if phase:
            out.append(Seed(
                family="element", key=f"{base}-p", subject=name,
                predicate="has phase at standard conditions", obj=phase,
                template=(f"At standard temperature and pressure {name} ({symbol}) "
                          f"is a {{obj}}."),
                evidence=f"PeriodicTableJSON: name={name} phase={phase}",
                source=src, context=where, difficulty="easy", aliases=(symbol,),
                gold_phrase=f"is a {phase}"))

        cat = e.get("category")
        if cat:
            out.append(Seed(
                family="element", key=f"{base}-c", subject=name,
                predicate="belongs to element category", obj=cat,
                template=f"{name} ({symbol}) is classified as a {{obj}}.",
                evidence=f"PeriodicTableJSON: name={name} category={cat}",
                source=src, context=where, difficulty="medium", aliases=(symbol,),
                gold_phrase=f"classified as a {cat}"))

        disc = e.get("discovered_by")
        if disc:
            out.append(Seed(
                family="element", key=f"{base}-d", subject=name,
                predicate="was discovered by", obj=disc,
                template=f"{name} ({symbol}) is credited as discovered by {{obj}}.",
                evidence=f"PeriodicTableJSON: name={name} discovered_by={disc}",
                source=src, context=where, difficulty="hard", aliases=(symbol,),
                gold_phrase=f"discovered by {disc}"))

        density = e.get("density")
        if density:
            dens_s = _num(density, 4)
            out.append(Seed(
                family="element", key=f"{base}-y", subject=name,
                predicate="has density", obj=dens_s,
                template=f"The density of {name} ({symbol}) is {{obj}} g/cm3.",
                evidence=f"PeriodicTableJSON: name={name} density={density}",
                source=src, context=where, difficulty="hard", aliases=(symbol,),
                gold_phrase=f"is {dens_s} g/cm3"))

        cfg = e.get("electron_configuration")
        if cfg:
            out.append(Seed(
                family="element", key=f"{base}-e", subject=name,
                predicate="has electron configuration", obj=cfg,
                template=f"The electron configuration of {name} ({symbol}) is {{obj}}.",
                evidence=(f"PeriodicTableJSON: name={name} "
                          f"electron_configuration={cfg}"),
                source=src, context=where, difficulty="hard", aliases=(symbol,),
                gold_phrase=f"is {cfg}"))

        melt = e.get("melt")
        if melt:
            melt_s = _num(melt, 2)
            out.append(Seed(
                family="element", key=f"{base}-t", subject=name,
                predicate="has melting point", obj=melt_s,
                template=f"The melting point of {name} ({symbol}) is {{obj}} K.",
                evidence=f"PeriodicTableJSON: name={name} melt={melt}",
                source=src, context=where, difficulty="hard", aliases=(symbol,),
                gold_phrase=f"is {melt_s} K"))

        boil = e.get("boil")
        if boil:
            boil_s = _num(boil, 2)
            out.append(Seed(
                family="element", key=f"{base}-b", subject=name,
                predicate="has boiling point", obj=boil_s,
                template=f"The boiling point of {name} ({symbol}) is {{obj}} K.",
                evidence=f"PeriodicTableJSON: name={name} boil={boil}",
                source=src, context=where, difficulty="hard", aliases=(symbol,),
                gold_phrase=f"is {boil_s} K"))

        shells = e.get("shells")
        if shells:
            shell_s = "-".join(str(s) for s in shells)
            out.append(Seed(
                family="element", key=f"{base}-s", subject=name,
                predicate="has electron shell occupancy", obj=shell_s,
                template=(f"The electron shell occupancy of {name} ({symbol}) "
                          f"is {{obj}}."),
                evidence=f"PeriodicTableJSON: name={name} shells={shells}",
                source=src, context=where, difficulty="hard", aliases=(symbol,),
                gold_phrase=f"is {shell_s}"))
    return out


def _country_seeds() -> list[Seed]:
    countries = _load_json("iso-3166.json")
    out: list[Seed] = []
    for c in countries:
        name = c.get("name")
        a2, a3 = c.get("alpha-2"), c.get("alpha-3")
        if not (name and a2 and a3):
            continue
        base = f"co-{_slug(name)}-{a2.lower()}"
        src = SOURCES["country"]
        region, sub = c.get("region"), c.get("sub-region")
        where = (f"It is recorded in the {region} region"
                 + (f", {sub} sub-region." if sub else ".") if region else "")

        out.append(Seed(
            family="country", key=f"{base}-a2", subject=name,
            predicate="has two-letter code", obj=a2,
            template=f"The country {name} is assigned the two-letter code {{obj}}.",
            evidence=f"ISO-3166: name={name} alpha-2={a2}",
            source=src, context=where, difficulty="easy", aliases=(a3,),
            gold_phrase=f"two-letter code {a2}"))

        out.append(Seed(
            family="country", key=f"{base}-a3", subject=name,
            predicate="has three-letter code", obj=a3,
            template=f"The country {name} is assigned the three-letter code {{obj}}.",
            evidence=f"ISO-3166: name={name} alpha-3={a3}",
            source=src, context=where, difficulty="medium", aliases=(a2,),
            gold_phrase=f"three-letter code {a3}"))

        if region:
            out.append(Seed(
                family="country", key=f"{base}-r", subject=name,
                predicate="belongs to region", obj=region,
                template=f"The country {name} belongs to the region {{obj}}.",
                evidence=f"ISO-3166: name={name} region={region}",
                source=src, context=where, difficulty="easy", aliases=(a2,),
                gold_phrase=f"region {region}"))

        if sub:
            out.append(Seed(
                family="country", key=f"{base}-s", subject=name,
                predicate="belongs to sub-region", obj=sub,
                template=f"The country {name} belongs to the sub-region {{obj}}.",
                evidence=f"ISO-3166: name={name} sub-region={sub}",
                source=src, context=where, difficulty="medium", aliases=(a2,),
                gold_phrase=f"sub-region {sub}"))

        num = c.get("numeric")
        if num:
            out.append(Seed(
                family="country", key=f"{base}-n", subject=name,
                predicate="has numeric code", obj=str(num),
                template=f"The country {name} is assigned the numeric code {{obj}}.",
                evidence=f"ISO-3166: name={name} numeric={num}",
                source=src, context=where, difficulty="hard", aliases=(a2,),
                gold_phrase=f"numeric code {num}"))

        ir = c.get("intermediate-region")
        if ir:
            out.append(Seed(
                family="country", key=f"{base}-i", subject=name,
                predicate="belongs to intermediate region", obj=ir,
                template=f"The country {name} belongs to the intermediate region {{obj}}.",
                evidence=f"ISO-3166: name={name} intermediate-region={ir}",
                source=src, context=where, difficulty="hard", aliases=(a2,),
                gold_phrase=f"intermediate region {ir}"))

        rc = c.get("region-code")
        if rc:
            out.append(Seed(
                family="country", key=f"{base}-rc", subject=name,
                predicate="has region code", obj=str(rc),
                template=f"The country {name} carries the region code {{obj}}.",
                evidence=f"ISO-3166: name={name} region-code={rc}",
                source=src, context=where, difficulty="hard", aliases=(a2,),
                gold_phrase=f"region code {rc}"))
    return out


def _mime_seeds() -> list[Seed]:
    mimes = _load_json("mime-db.json")
    out: list[Seed] = []
    for mtype, meta in sorted(mimes.items()):
        if "/" not in mtype or not isinstance(meta, dict):
            continue
        base = f"mi-{_slug(mtype)}"
        src = SOURCES["mime"]
        top, sub = mtype.split("/", 1)
        where = f"It is registered under the {top} top-level media type."

        charset = meta.get("charset")
        if charset:
            out.append(Seed(
                family="mime", key=f"{base}-cs", subject=mtype,
                predicate="declares charset", obj=charset,
                template=f"The media type {mtype} declares charset {{obj}}.",
                evidence=f"mime-db: {mtype} charset={charset}",
                source=src, context=where, difficulty="medium",
                gold_phrase=f"declares charset {charset}"))

        comp = meta.get("compressible")
        if comp is not None:
            word = "compressible" if comp else "non-compressible"
            out.append(Seed(
                family="mime", key=f"{base}-cp", subject=mtype,
                predicate="is marked compressible", obj=word,
                template=f"The media type {mtype} is marked {{obj}}.",
                evidence=f"mime-db: {mtype} compressible={comp}",
                source=src, context=where, difficulty="easy",
                gold_phrase=f"is marked {word}"))

        exts = meta.get("extensions")
        if exts:
            ext_s = ", ".join(exts)
            out.append(Seed(
                family="mime", key=f"{base}-ex", subject=mtype,
                predicate="has file extensions", obj=ext_s,
                template=(f"The media type {mtype} is associated with the file "
                          f"extensions {{obj}}."),
                evidence=f"mime-db: {mtype} extensions={exts}",
                source=src, context=where, difficulty="hard",
                gold_phrase=f"extensions {ext_s}"))

        source_param = meta.get("source")
        if source_param:
            out.append(Seed(
                family="mime", key=f"{base}-sr", subject=mtype,
                predicate="is sourced from", obj=source_param,
                template=f"The media type {mtype} is sourced from {{obj}}.",
                evidence=f"mime-db: {mtype} source={source_param}",
                source=src, context=where, difficulty="hard",
                gold_phrase=f"sourced from {source_param}"))

        out.append(Seed(
            family="mime", key=f"{base}-ty", subject=mtype,
            predicate="has subtype", obj=sub,
            template=f"The media type {mtype} has the subtype {{obj}}.",
            evidence=f"mime-db: {mtype} (top-level={top}, subtype={sub})",
            source=src, context=where, difficulty="easy",
            gold_phrase=f"subtype {sub}"))
    return out


def _city_seeds() -> list[Seed]:
    rows = _load_cities()
    out: list[Seed] = []
    for parts in rows:
        gid, name = parts[0], parts[1]
        lat, lon = parts[4], parts[5]
        cc, pop, tz = parts[8], parts[14], parts[17]
        if not (name and cc and pop.isdigit()):
            continue
        base = f"ci-{gid}"
        src = SOURCES["city"]
        label = f"{name} ({cc})"
        where = f"GeoNames records it under geonameid {gid} in country {cc}."

        out.append(Seed(
            family="city", key=f"{base}-p", subject=label,
            predicate="has population", obj=pop,
            template=f"The city of {label} has a recorded population of {{obj}}.",
            evidence=(f"GeoNames cities15000: geonameid={gid} name={name} "
                      f"country={cc} population={pop}"),
            source=src, context=where, difficulty="medium",
            gold_phrase=f"population of {pop}"))

        if tz:
            out.append(Seed(
                family="city", key=f"{base}-t", subject=label,
                predicate="lies in timezone", obj=tz,
                template=f"The city of {label} lies in the timezone {{obj}}.",
                evidence=(f"GeoNames cities15000: geonameid={gid} name={name} "
                          f"timezone={tz}"),
                source=src, context=where, difficulty="medium",
                gold_phrase=f"timezone {tz}"))

        if lat and lon:
            coord = f"{lat}, {lon}"
            out.append(Seed(
                family="city", key=f"{base}-g", subject=label,
                predicate="has coordinates", obj=coord,
                template=f"The city of {label} is located at coordinates {{obj}}.",
                evidence=(f"GeoNames cities15000: geonameid={gid} name={name} "
                          f"lat={lat} lon={lon}"),
                source=src, context=where, difficulty="hard",
                gold_phrase=f"coordinates {coord}"))

        out.append(Seed(
            family="city", key=f"{base}-c", subject=label,
            predicate="is located in country", obj=cc,
            template=f"The city of {label} is located in country {{obj}}.",
            evidence=(f"GeoNames cities15000: geonameid={gid} name={name} "
                      f"country={cc}"),
            source=src, context=where, difficulty="easy",
            gold_phrase=f"country {cc}"))
    return out


def _codepoint_seeds() -> list[Seed]:
    """Unicode Character Database — one row per assigned code point.

    UnicodeData.txt is semicolon-delimited with 15 fields; field 0 is the code
    point, 1 the name, 2 the general category, 3 the canonical combining class,
    4 the bidi class, 6 the decimal digit value, 12 the ISO comment.
    """
    path = REFERENCE_DIR / "UnicodeData.txt"
    if not path.is_file():
        raise FileNotFoundError(f"missing {path}")
    out: list[Seed] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\n").split(";")
            if len(f) < 15:
                continue
            cp, name, gcat, ccc, bidi = f[0], f[1], f[2], f[3], f[4]
            if not name or name.startswith("<"):
                continue  # control/private-use rows carry no real name
            try:
                cp_int = int(cp, 16)
            except ValueError:
                continue
            label = f"U+{cp}"
            base = f"cp-{cp.lower()}"
            src = SOURCES["codepoint"]
            where = (f"It is listed in the Unicode Character Database with "
                     f"general category {gcat} and bidirectional class {bidi}.")

            out.append(Seed(
                family="codepoint", key=f"{base}-n", subject=label,
                predicate="has character name", obj=name,
                template=f"The Unicode code point {label} has the character name {{obj}}.",
                evidence=f"UnicodeData.txt: {cp};{name};{gcat};{ccc};{bidi}",
                source=src, context=where, difficulty="medium",
                gold_phrase=f"character name {name}"))

            out.append(Seed(
                family="codepoint", key=f"{base}-g", subject=label,
                predicate="has general category", obj=gcat,
                template=f"The Unicode code point {label} has the general category {{obj}}.",
                evidence=f"UnicodeData.txt: {cp};{name};{gcat}",
                source=src, context=where, difficulty="easy",
                gold_phrase=f"general category {gcat}"))

            out.append(Seed(
                family="codepoint", key=f"{base}-b", subject=label,
                predicate="has bidirectional class", obj=bidi,
                template=f"The Unicode code point {label} has the bidirectional class {{obj}}.",
                evidence=f"UnicodeData.txt: {cp};{name};{gcat};{ccc};{bidi}",
                source=src, context=where, difficulty="hard",
                gold_phrase=f"bidirectional class {bidi}"))

            out.append(Seed(
                family="codepoint", key=f"{base}-d", subject=label,
                predicate="has decimal value", obj=str(cp_int),
                template=f"The Unicode code point {label} has the decimal value {{obj}}.",
                evidence=f"UnicodeData.txt: {cp} (hex) = {cp_int} (decimal)",
                source=src, context=where, difficulty="hard",
                gold_phrase=f"decimal value {cp_int}"))

            if ccc and ccc != "0":
                out.append(Seed(
                    family="codepoint", key=f"{base}-c", subject=label,
                    predicate="has combining class", obj=ccc,
                    template=f"The Unicode code point {label} has the canonical combining class {{obj}}.",
                    evidence=f"UnicodeData.txt: {cp};{name};{gcat};{ccc}",
                    source=src, context=where, difficulty="hard",
                    gold_phrase=f"combining class {ccc}"))
    return out


def _countrymeta_seeds() -> list[Seed]:
    """mledoze/countries — capital, currency, TLD, calling code, languages."""
    data = _load_json("countries-mledoze.json")
    out: list[Seed] = []
    for c in data:
        name = (c.get("name") or {}).get("common")
        cca2, cca3 = c.get("cca2"), c.get("cca3")
        if not (name and cca2 and cca3):
            continue
        base = f"cm-{cca2.lower()}"
        src = SOURCES["countrymeta"]
        region = c.get("region")
        where = (f"It is recorded with the three-letter code {cca3}"
                 + (f" in the {region} region." if region else "."))

        caps = c.get("capital") or []
        if caps:
            cap = caps[0]
            out.append(Seed(
                family="countrymeta", key=f"{base}-cap", subject=name,
                predicate="has capital city", obj=cap,
                template=f"The capital city of {name} is {{obj}}.",
                evidence=f"mledoze/countries: {name} capital={caps}",
                source=src, context=where, difficulty="easy", aliases=(cca3,),
                gold_phrase=f"capital city of {name} is {cap}"))

        tlds = c.get("tld") or []
        if tlds:
            tld = tlds[0]
            out.append(Seed(
                family="countrymeta", key=f"{base}-tld", subject=name,
                predicate="has top-level domain", obj=tld,
                template=f"The country {name} is assigned the top-level domain {{obj}}.",
                evidence=f"mledoze/countries: {name} tld={tlds}",
                source=src, context=where, difficulty="medium", aliases=(cca3,),
                gold_phrase=f"top-level domain {tld}"))

        cur = c.get("currencies") or {}
        if cur:
            code = sorted(cur)[0]
            cname = (cur[code] or {}).get("name") or code
            out.append(Seed(
                family="countrymeta", key=f"{base}-cur", subject=name,
                predicate="uses currency", obj=f"{cname} ({code})",
                template=f"The country {name} uses the currency {{obj}}.",
                evidence=f"mledoze/countries: {name} currencies={cur}",
                source=src, context=where, difficulty="medium", aliases=(cca3,),
                gold_phrase=f"currency {cname} ({code})"))

        langs = c.get("languages") or {}
        if langs:
            lcode = sorted(langs)[0]
            lname = langs[lcode]
            out.append(Seed(
                family="countrymeta", key=f"{base}-lang", subject=name,
                predicate="has official language", obj=lname,
                template=f"The country {name} records {lname} as an official language.",
                evidence=f"mledoze/countries: {name} languages={langs}",
                source=src, context=where, difficulty="medium", aliases=(cca3,),
                gold_phrase=f"records {lname} as an official language"))

        idd = c.get("idd") or {}
        root, suffixes = idd.get("root"), idd.get("suffixes") or []
        if root and suffixes:
            dial = f"{root}{suffixes[0]}"
            out.append(Seed(
                family="countrymeta", key=f"{base}-dial", subject=name,
                predicate="has calling code", obj=dial,
                template=f"The country {name} has the international calling code {{obj}}.",
                evidence=f"mledoze/countries: {name} idd={idd}",
                source=src, context=where, difficulty="hard", aliases=(cca3,),
                gold_phrase=f"calling code {dial}"))

        area = c.get("area")
        if isinstance(area, (int, float)) and area > 0:
            area_s = _num(area, 2)
            out.append(Seed(
                family="countrymeta", key=f"{base}-area", subject=name,
                predicate="has area", obj=area_s,
                template=f"The country {name} has a recorded area of {{obj}} square kilometres.",
                evidence=f"mledoze/countries: {name} area={area}",
                source=src, context=where, difficulty="hard", aliases=(cca3,),
                gold_phrase=f"area of {area_s} square kilometres"))

        borders = c.get("borders") or []
        if borders:
            b = ", ".join(borders)
            out.append(Seed(
                family="countrymeta", key=f"{base}-bord", subject=name,
                predicate="borders", obj=b,
                template=f"The country {name} shares a land border with {{obj}}.",
                evidence=f"mledoze/countries: {name} borders={borders}",
                source=src, context=where, difficulty="hard", aliases=(cca3,),
                gold_phrase=f"border with {b}"))
    return out


def _dossier_seeds(families: dict[str, list[Seed]]) -> list[Seed]:
    """One verbose record per entity, aggregating every true field we hold.

    Every value in a dossier came from the same cached source as the atomic
    record it was taken from, so the dossier is grounded for the same reason
    the atomic facts are — it is a wider view of the same evidence, not a new
    claim. This is what makes the corpus realistic as a memory store: real
    notes are multi-field, not one predicate per line.
    """
    grouped: dict[tuple[str, str], list[Seed]] = {}
    for fam, seeds in families.items():
        for s in seeds:
            grouped.setdefault((fam, s.subject), []).append(s)

    out: list[Seed] = []
    for (fam, subject), seeds in grouped.items():
        if len(seeds) < 2:
            continue
        first = seeds[0]
        parts = [f"{s.predicate} {s.obj}" for s in seeds]
        body = "; ".join(parts)
        content = f"Record for {subject}: {body}."
        evidence = " | ".join(s.evidence for s in seeds)
        out.append(Seed(
            family=f"{fam}-dossier",
            key=f"do-{fam}-{_slug(subject)}",
            subject=subject,
            predicate="has recorded attributes",
            obj=first.obj,
            template=content.replace("{", "{{").replace("}", "}}"),
            evidence=evidence,
            source=first.source,
            context="",
            difficulty="hard",
            aliases=first.aliases,
            gold_phrase=first.gold_phrase))
    return out


def _interleave(families: dict[str, list[Seed]], limit: int,
                extra: list[Seed] | None = None) -> list[Seed]:
    """Round-robin with a per-family cap, then a fill pass.

    The cap stops one family (city has 34k rows, codepoint 165k) from
    swallowing the category. The fill pass then tops the corpus up from
    whatever is left, so a target larger than the capped sum is still
    reachable. The realised mix is reported in the manifest, not assumed.

    Driven by a `progressed` flag, not an outer cursor guard: a guard on a
    local cursor never changes and spins forever.
    """
    caps = {fam: int(limit * FAMILY_CAP[fam]) for fam in families}
    taken = {fam: 0 for fam in families}
    out: list[Seed] = []
    seen: set[str] = set()
    i = 0
    while len(out) < limit:
        progressed = False
        for fam, seeds in families.items():
            if i < len(seeds) and taken[fam] < caps[fam]:
                progressed = True
                s = seeds[i]
                if s.key not in seen:
                    seen.add(s.key)
                    out.append(s)
                    taken[fam] += 1
                    if len(out) >= limit:
                        break
        if not progressed:
            break
        i += 1

    # Fill pass: capped families are exhausted, so take the remainder from the
    # pools that still have rows, round-robin so the mix stays spread.
    if len(out) < limit:
        cursors = {fam: 0 for fam in families}
        while len(out) < limit:
            progressed = False
            for fam, seeds in families.items():
                while cursors[fam] < len(seeds):
                    s = seeds[cursors[fam]]
                    cursors[fam] += 1
                    if s.key not in seen:
                        seen.add(s.key)
                        out.append(s)
                        progressed = True
                        break
                if len(out) >= limit:
                    break
            if not progressed:
                break
    # Last resort: the verbose dossier tier, which is still grounded on the same
    # cached evidence. Only reached when the atomic pools are exhausted.
    if len(out) < limit and extra:
        for s in extra:
            if len(out) >= limit:
                break
            if s.key not in seen:
                seen.add(s.key)
                out.append(s)
    return out


def grounded_seeds(limit: int) -> list[Seed]:
    families = {"element": _element_seeds(), "country": _country_seeds(),
                "mime": _mime_seeds(), "city": _city_seeds(),
                "codepoint": _codepoint_seeds(),
                "countrymeta": _countrymeta_seeds()}
    # Dossiers are the verbose tier: they carry the same evidence as the atomic
    # records, aggregated per entity. They are appended after the atomic pool so
    # the atomic facts always win a slot first.
    dossiers = _dossier_seeds(families)
    return _interleave(families, limit, extra=dossiers)


# ---------------------------------------------------------------------------
# ungrounded universe (fictional, internally consistent, no source)
# ---------------------------------------------------------------------------

_ORG_A = ("Halden", "Tessaly", "Orvyx", "Calder", "Nimbari", "Quillon",
          "Vasterly", "Merrow", "Dravent", "Solvane", "Pellow", "Skarn",
          "Aurelis", "Brantwell", "Corvani", "Illworth", "Marrowgate",
          "Sablewick", "Thornbury", "Veyland")
_ORG_B = ("Logistics", "Labs", "Foundry", "Analytics", "Systems", "Dynamics",
          "Works", "Collective", "Reach", "Union")
_CITY = ("Alderhow", "Brackmoor", "Cassavale", "Dunmarch", "Elderfen",
         "Fallcrest", "Glimmervik", "Harrowgate", "Ivymount", "Jessup",
         "Kaldrast", "Lowmarsh", "Mirrhaven", "Northgate", "Oakspire",
         "Pellumbra", "Quarryden", "Rookhaven", "Stonewold", "Tarnwick")
_ROLE = ("chief archivist", "head of retrieval", "reliability lead",
         "platform steward", "data custodian", "index warden",
         "continuity officer")
_PRODUCT = ("Loom", "Kestrel", "Vellum", "Anvil", "Beacon", "Cinder",
            "Drift", "Ember", "Fathom", "Gale")
_POLICY = ("retention window", "replication factor", "audit cadence",
           "cold-tier threshold", "shard rebalance interval")
_FIRST = ("Ash", "Bex", "Corin", "Dara", "Ewan", "Fen", "Gwen", "Hale",
          "Ivo", "Jory", "Kesh", "Lune")


def ungrounded_seeds(limit: int) -> list[Seed]:
    out: list[Seed] = []
    for i in range(limit):
        key = f"ug-{i:06d}"
        r = _rng(key)
        org = f"{r.choice(_ORG_A)} {r.choice(_ORG_B)}"
        city = r.choice(_CITY)
        kind = i % 7

        if kind == 0:
            badge = 1000 + i
            pred, obj = "operates cluster under badge", f"R-{badge}"
            tmpl = (f"{org} operates a retrieval cluster in {city} under "
                    f"internal badge {{obj}}, reporting to the "
                    f"{r.choice(_ROLE)}.")
            ctx = (f"The cluster was commissioned in {2014 + (i % 12)} and "
                   f"serves the {city} engineering group.")
            diff = "easy"
        elif kind == 1:
            head = 4 + (i % 40)
            pred, obj = "splits workload across shards", str(head)
            tmpl = (f"{org} splits its {city} workload across {{obj}} shards "
                    f"and reviews shard balance every {6 + (i % 5)} weeks.")
            ctx = (f"Shard placement is decided by the {city} capacity board "
                   f"and re-checked after every release.")
            diff = "medium"
        elif kind == 2:
            ver = f"{2 + (i % 9)}.{i % 7}.{i % 5}"
            pred, obj = "pins ingestion pipeline at", ver
            tmpl = (f"{org} pins the {city} ingestion pipeline at release "
                    f"{{obj}} and freezes schema changes during audits.")
            ctx = (f"The pin is lifted only after the {city} audit board signs "
                   f"off on the migration plan.")
            diff = "medium"
        elif kind == 3:
            person = f"{r.choice(_FIRST)} {r.choice(_ORG_A)}"
            role = r.choice(_ROLE)
            pred, obj = "serves as", role
            tmpl = (f"{person} serves as {{obj}} at {org}, covering the "
                    f"{city} region since {2015 + (i % 11)}.")
            ctx = (f"The role reports into the {org} operating committee and "
                   f"owns the {city} continuity plan.")
            diff = "easy"
        elif kind == 4:
            price = 40 + (i % 460)
            pred, obj = "is priced at", f"{price} credits"
            tmpl = (f"The {r.choice(_PRODUCT)} tier from {org} is priced at "
                    f"{{obj}} per month for the {city} deployment.")
            ctx = (f"Pricing is reviewed quarterly against the {city} "
                   f"procurement schedule.")
            diff = "medium"
        elif kind == 5:
            days = 30 + (i % 700)
            pred, obj = "sets retention window to", f"{days} days"
            tmpl = (f"{org} sets its {r.choice(_POLICY)} to {{obj}} for all "
                    f"records ingested through the {city} gateway.")
            ctx = (f"The setting is enforced by the {city} gateway and audited "
                   f"by the {org} compliance desk.")
            diff = "hard"
        else:
            pop = 12000 + (i * 37) % 900000
            pred, obj = "has population", str(pop)
            tmpl = (f"The settlement of {city} in the {r.choice(_ORG_A)} "
                    f"district has a recorded population of {{obj}}.")
            ctx = (f"The district census is compiled by the {city} registry "
                   f"office every {2 + (i % 4)} years.")
            diff = "easy"

        out.append(Seed(
            family="fiction", key=key, subject=org, predicate=pred, obj=obj,
            template=tmpl, evidence="", source=None, context=ctx,
            difficulty=diff))
    return out


# ---------------------------------------------------------------------------
# false facts: deterministic mutations of grounded records
# ---------------------------------------------------------------------------

def _restates_truth(content: str, asserted: str, true_value: str) -> bool:
    """True if the text also states the value the claim is denying.

    Word-bounded, and the asserted value is removed first, because the true
    value is often a substring of the asserted one ("compressible" inside
    "non-compressible") and short values ("AF", "Po") occur inside words.
    """
    if not true_value:
        return False
    text = content.replace(asserted, " ") if asserted else content
    pattern = r"(?<![A-Za-z0-9])" + re.escape(true_value) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def false_seeds(grounded: list[Seed], limit: int) -> list[Seed]:
    """Swap the object for another record's object in the same family+predicate.

    Keyed by (family, predicate) so a swap never puts an atomic symbol where a
    paragraph belongs — a mismatched swap is nonsense, not a plausible wrong
    answer. `object` holds the WRONG value (what the claim asserts);
    `true_value` holds what the grounded record actually says.
    """
    pools: dict[tuple[str, str], list[Seed]] = {}
    for g in grounded:
        pools.setdefault((g.family, g.predicate), []).append(g)

    # Distinct values per (family, predicate). Picking a donor *record* fails
    # whenever the pool's values are mostly identical (e.g. "has general
    # category" has ~30 distinct values across 30k records), which silently
    # starves the false category. Pick a different VALUE instead.
    values: dict[tuple[str, str], list[str]] = {}
    for k, seeds in pools.items():
        seen_vals: list[str] = []
        for s in seeds:
            if s.obj not in seen_vals:
                seen_vals.append(s.obj)
        values[k] = seen_vals

    out: list[Seed] = []
    seen: set[str] = set()
    for idx, g in enumerate(grounded):
        if len(out) >= limit:
            break
        k = (g.family, g.predicate)
        vals = values[k]
        if len(vals) < 2:
            continue
        key = f"fa-{g.key}"
        if key in seen:
            continue
        # The claim must assert ONLY the wrong value. Two ways the true value
        # sneaks back in: the context sentence restates it ("...in country BR"),
        # and the template itself embeds it ("The media type
        # application/1d-interleaved-parityfec has the subtype X" — the true
        # subtype is in the subject). Walk the distinct values until one yields
        # a clean claim; only skip the record if none does.
        pos = vals.index(g.obj)
        chosen = None
        for step in range(1, len(vals)):
            wrong = vals[(pos + step) % len(vals)]
            if wrong == g.obj:
                continue
            content = g.template.format(obj=wrong)
            if g.context:
                content = f"{content} {g.context}"
            if _restates_truth(content, wrong, g.obj):
                content = f"{g.subject} — {g.predicate}: {wrong}."
                if _restates_truth(content, wrong, g.obj):
                    continue
            chosen = (wrong, content)
            break
        if chosen is None:
            continue
        wrong, content = chosen
        seen.add(key)
        out.append(Seed(
            family=g.family,
            key=key,
            subject=g.subject,
            predicate=g.predicate,
            obj=wrong,                     # the wrong value the claim asserts
            template=content.replace("{", "{{").replace("}", "}}"),
            evidence=g.evidence,
            source=None,
            context="",
            difficulty=g.difficulty,
            aliases=(g.key,),              # contradicts target
            gold_phrase=g.gold_phrase,
            true_value=g.obj))             # what the truth actually holds
    return out


# ---------------------------------------------------------------------------
# probes
# ---------------------------------------------------------------------------

def _safe_text(candidates: list[str], needle: str) -> str | None:
    """Return the first candidate that does not contain the answer.

    A probe whose text contains its own expected evidence is not a retrieval
    task, it is an echo. Some predicates embed the answer word ("is marked
    compressible"), so a template built from the predicate leaks by
    construction. Fall back to progressively more neutral phrasings, and
    return None if even the subject leaks — the caller then skips that record
    rather than emitting an unanswerable probe.
    """
    low = needle.lower()
    for text in candidates:
        if text and low not in text.lower():
            return text
    return None


def build_probes(grounded: list[Seed], false: list[Seed],
                 n_direct: int, n_adversarial: int,
                 n_contradiction: int, n_unanswerable: int) -> list[dict]:
    """Probes that are answerable by construction.

    Every non-control probe names a gold record that IS in the corpus, and the
    expected evidence does NOT appear in the probe text. The validator enforces
    both, so an answer-free probe cannot be generated by accident.
    """
    probes: list[dict] = []
    alias_pool = [g for g in grounded if g.aliases] or grounded

    def add_direct(i: int, g: Seed) -> None:
        text = _safe_text([
            f"What is the {g.predicate} of {g.subject}?",
            f"What is recorded for {g.subject}?",
            f"Look up the record for {g.subject}.",
        ], g.gold_phrase)
        if text is None:
            return
        probes.append({
            "qid": f"q-direct-{i:04d}", "kind": "direct", "text": text,
            "expect": [g.gold_phrase], "gold_key": g.key,
            "difficulty": g.difficulty,
        })

    def add_adversarial(i: int, g: Seed) -> None:
        alias = g.aliases[0]
        text = _safe_text([
            f"Under the designator {alias}, what is recorded for {g.predicate}?",
            f"Under the designator {alias}, what does the record hold?",
            f"Look up the entry filed under {alias}.",
        ], g.gold_phrase)
        if text is None:
            return
        probes.append({
            "qid": f"q-adversarial-{i:04d}", "kind": "adversarial", "text": text,
            "expect": [g.gold_phrase], "gold_key": g.key, "difficulty": "hard",
        })

    def add_contradiction(i: int, f: Seed) -> None:
        text = _safe_text([
            (f"A claim states that {f.subject} has {f.predicate} {f.obj}. "
             f"What does the record actually say?"),
            (f"A claim about {f.subject} asserts {f.obj}. "
             f"What does the record actually say?"),
            f"A claim about {f.subject} is disputed. What does the record say?",
        ], f.gold_phrase)
        if text is None:
            return
        probes.append({
            "qid": f"q-contradiction-{i:04d}", "kind": "contradiction",
            "text": text, "expect": [f.gold_phrase],
            "gold_key": f.aliases[0], "difficulty": "hard",
        })

    # Walk the pools with a stride so a skipped record does not collapse the
    # class: keep advancing until the requested count is actually reached.
    def fill(kind: str, pool: list[Seed], want: int, emit) -> None:
        made = 0
        stride = 7 if kind == "direct" else 11
        for step in range(len(pool) * 2):
            if made >= want:
                break
            emit(made, pool[(step * stride) % len(pool)])
            made = sum(1 for p in probes if p["kind"] == kind)
        if made < want:
            raise AssertionError(
                f"{kind}: only {made} of {want} probes could be built without "
                "leaking their own answer")

    fill("direct", grounded, n_direct, add_direct)
    fill("adversarial", alias_pool, n_adversarial, add_adversarial)
    if false:
        fill("contradiction", false, n_contradiction, add_contradiction)

    for i in range(n_unanswerable):
        r = _rng(f"control-{i}")
        probes.append({
            "qid": f"q-unanswerable-{i:04d}",
            "kind": "unanswerable",
            "text": (f"What is the {r.choice(_POLICY)} of "
                     f"{r.choice(_ORG_A)} {r.choice(_ORG_B)} in "
                     f"{r.choice(_CITY)}?"),
            "expect": [],
            "gold_key": None,
            "difficulty": "control",
        })
    return probes


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------

def _row(seed: Seed, category: str, idx: int) -> dict:
    prefix = {"grounded": "g", "ungrounded": "u", "false": "f"}[category]
    content = seed.template.format(obj=seed.obj)
    if seed.context:
        content = f"{content} {seed.context}"
    return {
        "id": f"{prefix}{idx:07d}",
        "key": seed.key,
        "category": category,
        "family": seed.family,
        "topic": f"bench.v3.{seed.family}",
        "content": content,
        "tags": [seed.family, category, "bench-v3"],
        "epistemic_status": EPISTEMIC[category],
        "subject": seed.subject,
        "predicate": seed.predicate,
        "object": seed.obj,
        "confidence": {"grounded": 1.0, "ungrounded": 0.4, "false": 0.2}[category],
        "source": seed.source if category == "grounded" else None,
        "evidence": seed.evidence if category == "grounded" else None,
        "contradicts": seed.aliases[0] if category == "false" else None,
        "true_value": seed.true_value if category == "false" else None,
        "difficulty": seed.difficulty,
        "timestamp": _ts(seed.key),
        "schema_version": SCHEMA_VERSION,
        "provenance": {
            "generator": "benchmarks/v3/build_corpus_v3.py",
            "seed": SEED,
            "retrieved": RETRIEVED if category == "grounded" else None,
            "source_url": seed.source if category == "grounded" else None,
        },
    }


def build(per_category: int) -> tuple[list[dict], list[dict]]:
    """Build the corpus with an exactly balanced three-way split.

    Not every grounded record can be falsified: a claim about
    ``application/1d-interleaved-parityfec`` cannot deny its own subtype
    without naming it, because the true value is inside the subject. Those
    records are skipped rather than turned into self-contradicting "false"
    claims, so the false pool is the binding constraint. Grounded and
    ungrounded are then trimmed to its size, which makes the split exactly
    1/3 each instead of "roughly" — a documented, measured balance rather than
    an approximate one.
    """
    grounded_pool = grounded_seeds(per_category)
    # Iterate to a fixed point: trimming the grounded list changes the distinct
    # value pools, which can make a few more records unfalsifiable. Loop until
    # the set stops shrinking, so every false record's `contradicts` target is
    # present in the shipped corpus and the two counts match exactly.
    grounded = grounded_pool
    for _ in range(10):
        false = false_seeds(grounded, len(grounded))
        falsifiable = {f.aliases[0] for f in false}
        trimmed = [g for g in grounded if g.key in falsifiable]
        if len(trimmed) == len(grounded):
            break
        grounded = trimmed
    false = false_seeds(grounded, len(grounded))
    if len(false) != len(grounded):
        raise SystemExit(
            f"false/grounded mismatch after trim: {len(false)} vs {len(grounded)}")
    n = len(grounded)
    if n == 0:
        raise SystemExit("no falsifiable grounded records; cannot build corpus")
    ungrounded = ungrounded_seeds(n)

    rows: list[dict] = []
    for i, s in enumerate(grounded):
        rows.append(_row(s, "grounded", i))
    for i, s in enumerate(ungrounded):
        rows.append(_row(s, "ungrounded", i))
    for i, s in enumerate(false):
        rows.append(_row(s, "false", i))

    probes = build_probes(grounded, false, 200, 150, 150, 100)
    return rows, probes


def _write_jsonl(path: Path, rows: list[dict]) -> int:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    # Strip-aware count: a missing trailing newline must not shave a record.
    with path.open(encoding="utf-8") as fh:
        n = sum(1 for line in fh if line.strip())
    if n != len(rows):
        raise AssertionError(f"{path.name}: wrote {len(rows)} rows, read {n}")
    return n


def write_corpus(out_dir: Path, per_category: int, shard_bytes: int) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, probes = build(per_category)

    # Shard by serialized size so no single file approaches GitHub's 100 MB
    # hard limit. Shards are contiguous slices of the same record order.
    shards: list[list[dict]] = [[]]
    size = 0
    for row in rows:
        line = len(json.dumps(row, ensure_ascii=False).encode("utf-8")) + 1
        if size + line > shard_bytes and shards[-1]:
            shards.append([])
            size = 0
        shards[-1].append(row)
        size += line

    shard_files = []
    for i, shard in enumerate(shards, start=1):
        name = f"records.part-{i:02d}.jsonl"
        n = _write_jsonl(out_dir / name, shard)
        shard_files.append({
            "file": name,
            "records": n,
            "bytes": (out_dir / name).stat().st_size,
        })

    _write_jsonl(out_dir / "probes.jsonl", probes)

    by_category: dict[str, int] = {}
    by_family: dict[str, int] = {}
    for row in rows:
        by_category[row["category"]] = by_category.get(row["category"], 0) + 1
        by_family[row["family"]] = by_family.get(row["family"], 0) + 1

    total_bytes = sum(s["bytes"] for s in shard_files)
    manifest = {
        "name": CORPUS_NAME,
        "schema_version": SCHEMA_VERSION,
        "seed": SEED,
        "records": len(rows),
        "by_category": by_category,
        "by_family": by_family,
        "probes": len(probes),
        "probe_kinds": _count_kinds(probes),
        "shards": shard_files,
        "total_bytes": total_bytes,
        "bytes_per_record": round(total_bytes / len(rows), 2),
        "sources": SOURCES,
        "generator": "benchmarks/v3/build_corpus_v3.py",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _count_kinds(probes: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in probes:
        out[p["kind"]] = out.get(p["kind"], 0) + 1
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-category", type=int, default=30000,
                    help="records per category (total = 3x this)")
    ap.add_argument("--out", default="benchmarks/corpora/v3")
    ap.add_argument("--shard-bytes", type=int, default=35 * 1024 * 1024)
    args = ap.parse_args(argv)

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    man = write_corpus(out, args.per_category, args.shard_bytes)
    print(json.dumps(man, indent=2))
    print(f"\nwrote {man['records']} records / {man['total_bytes']} bytes "
          f"({man['total_bytes'] / 1048576:.2f} MiB) under {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
