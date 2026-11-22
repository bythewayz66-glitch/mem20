#!/usr/bin/env python3
"""Generate the mem20 /series/ reader pages from what actually exists in the repo.

Sources (measured, never remembered):
  comics/the-z-corps/issue-NN/*.pdf                -> finished comic issues
  comics/the-z-corps/issue-NN/*Shooting_Script.md  -> per-page beats
  docs/app/narrative/serial-*.md                   -> chronicle installments

Writes, all under docs/series/ and all reusing series.css + analytics.js:
  comic/issue-NN.html, chronicles/NNN.html
  comic/index.html, chronicles/index.html, index.html
  data/comic-issues.json, data/chronicles.json, chronicles/feed.xml

Markup lives in _tpl.py and _idx.py, markdown in _md.py, so each file stays
small.

Run: python3 docs/series/_build.py && python3 docs/series/_verify.py
"""
import datetime
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
S = HERE
RAW = "https://raw.githubusercontent.com/bythewayz66-glitch/mem20/main"
SITE = "https://mem20.com"

sys.path.insert(0, HERE)
import _idx    # noqa: E402
import _md     # noqa: E402
import _tpl    # noqa: E402

esc = lambda s: html.escape(str(s), quote=True)
inline = _md.inline
md = _md.md


# ------------------------------------------------------------------ comics

def pdf_pages(path):
    """Stream for /Type /Page markers; never load a 50 MB PDF into memory."""
    n, tail = 0, b""
    try:
        with open(path, "rb") as f:
            while True:
                c = f.read(1 << 20)
                if not c:
                    break
                d = tail + c
                n += len(re.findall(rb"/Type\s*/Page[^s]", d))
                tail = d[-32:]
    except Exception:
        return None
    return n or None


def beats(script):
    """Page beats come in two shapes across the issues:

    * issues 01-05: `## PAGE N — TITLE` headings
    * issues 06-12: a `| # | Page | Beat | Source |` table under "PAGE BY PAGE"

    Both are read; whichever the issue uses is what its reader page lists.
    """
    if not script or not os.path.exists(script):
        return []
    text = open(script, encoding="utf-8", errors="ignore").read()

    out = []
    for line in text.split("\n"):
        m = re.match(r"^##\s+PAGE\s+(\d+)\s*[\u2014\u2013-]\s*(.+?)\s*$", line.strip())
        if m:
            out.append((int(m.group(1)), m.group(2)))
    if out:
        return out

    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        c = [x.strip() for x in s.strip("|").split("|")]
        if len(c) < 3 or not re.fullmatch(r"\d+", c[0]):
            continue
        out.append((int(c[0]), c[1] or c[2]))
    return out


def comics():
    out = []
    for d in sorted(glob.glob(os.path.join(REPO, "comics/the-z-corps/issue-[0-9][0-9]"))):
        num = int(re.search(r"issue-(\d+)", d).group(1))
        pdfs = glob.glob(os.path.join(d, "*.pdf"))
        if not pdfs:
            continue
        pdf = pdfs[0]
        scripts = glob.glob(os.path.join(d, "*Shooting_Script.md"))
        title = window = source = None
        if scripts:
            t = open(scripts[0], encoding="utf-8", errors="ignore").read()
            m = re.search(r'^#\s+THE Z CORPS #\d+\s+[\u2014-]\s+"?(.+?)"?\s*$', t, re.M)
            title = m.group(1).strip().strip('"') if m else None
            m = re.search(r"\*\*Window:\*\*\s*(.+)", t)
            window = m.group(1).strip() if m else None
            m = re.search(r"\*\*Source:\*\*\s*(.+)", t)
            source = m.group(1).strip() if m else None
        if not title:
            title = os.path.basename(pdf)[:-4].split("_", 3)[-1].replace("_", " ")
        rel = os.path.relpath(pdf, REPO).replace(os.sep, "/")
        out.append(dict(number=num, title=title, rel=rel, url="%s/%s" % (RAW, rel),
                        size=os.path.getsize(pdf), pages=pdf_pages(pdf),
                        window=window, source=source,
                        beats=beats(scripts[0] if scripts else None)))
    return out


# ------------------------------------------------------------------ chronicles

META = ("What this document", "What this post cannot", "Standing of", "Corrections to earlier",
        "Sources read", "Evidence block", "The verifier", "Where this post begins",
        "The window in numbers", "What the failures corpus", "Appendix", "Method",
        "What moved", "Why this is a note")

SERIALS = ["serial-2026-10-27.md", "serial-2026-11-01.md", "serial-2026-11-01b.md",
           "serial-2026-11-21.md", "serial-2026-11-21b.md"]


def chronicles():
    out, seen = [], set()
    for fn in SERIALS:
        p = os.path.join(REPO, "docs/app/narrative", fn)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8", errors="ignore").read()
        date = re.search(r"serial-(\d{4}-\d{2}-\d{2})", fn).group(1)
        parts = re.split(r"^## (\d+)\. (.+)$", t, flags=re.M)
        for k in range(1, len(parts), 3):
            title, body = parts[k + 1].strip(), parts[k + 2]
            if any(m in title for m in META) or title.lower() in seen:
                continue
            body = re.split(r"^## \d+\. ", body, flags=re.M)[0]
            body = re.sub(r"^---\s*$", "", body, flags=re.M).strip()
            if len(body) < 200:
                continue
            seen.add(title.lower())
            out.append(dict(title=title, date=date, src=fn, body=body,
                            words=len(re.findall(r"\w+", body))))
    for i, e in enumerate(out, 1):
        e["n"] = i
    return out


# ------------------------------------------------------------------ data

def rfc822(d):
    return datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")


def write_data(its, es):
    ci = {
        "series": "The Comicbook Artist", "property": "mem20-series-01",
        "canonical_home": "%s/series/comic/" % SITE, "canon_owner": "Comicbook Artist",
        "format": "sequential art, numbered issues", "updated": "2026-11-21",
        "state_legend": {"ready": "art exists and is linked at its own URL",
                         "in_production": "art is being drawn now",
                         "planned": "canon exists, art not started"},
        "counts": {"issues": len(its), "ready": len(its)},
        "issues": [{"number": i["number"], "title": i["title"].title(), "state": "ready",
                    "pages": i["pages"],
                    "pages_url": "%s/series/comic/issue-%02d.html" % (SITE, i["number"]),
                    "pdf_url": i["url"], "pdf_path": i["rel"],
                    "window": i["window"], "source": i["source"]} for i in its],
    }
    json.dump(ci, open(os.path.join(S, "data/comic-issues.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    ch = {
        "series": "Mem20-naration's Chronicles", "property": "mem20-series-02",
        "canonical_home": "%s/series/chronicles/" % SITE, "author": "Mem20-naration",
        "cadence": "per installment", "updated": "2026-11-21",
        "origin_legend": {"grounded": "reports something that happened and can be checked",
                          "simulated": "a hypothesis the system is entertaining, not a record"},
        "counts": {"installments": len(es)},
        "entries": [{"installment": e["n"], "date": e["date"], "title": e["title"],
                     "origin": "grounded",
                     "url": "%s/series/chronicles/%03d.html" % (SITE, e["n"]),
                     "source_file": "docs/app/narrative/%s" % e["src"],
                     "summary": re.sub(r"\s+", " ", e["body"])[:280].strip()} for e in es],
    }
    json.dump(ch, open(os.path.join(S, "data/chronicles.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    items = "".join("""    <item>
      <title>%s</title>
      <link>%s/series/chronicles/%03d.html</link>
      <guid isPermaLink="true">%s/series/chronicles/%03d.html</guid>
      <pubDate>%s</pubDate>
      <category>grounded</category>
      <description>%s</description>
    </item>
""" % (esc(e["title"]), SITE, e["n"], SITE, e["n"], rfc822(e["date"]),
       esc(re.sub(r"\s+", " ", e["body"])[:400].strip())) for e in reversed(es))

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Mem20-naration's Chronicles</title>
    <link>%s/series/chronicles/</link>
    <atom:link href="%s/series/chronicles/feed.xml" rel="self" type="application/rss+xml"/>
    <description>A record of what the mem20 system actually did. Every installment is origin-tagged grounded or simulated.</description>
    <language>en</language>
    <lastBuildDate>%s</lastBuildDate>
%s  </channel>
</rss>
""" % (SITE, SITE, rfc822(es[-1]["date"]), items)
    open(os.path.join(S, "chronicles/feed.xml"), "w", encoding="utf-8").write(xml)


# ------------------------------------------------------------------ main

def main():
    its, es = comics(), chronicles()
    print("comics: %d  chronicles: %d" % (len(its), len(es)))
    if not its or not es:
        sys.exit("refusing to write: empty corpus")

    os.makedirs(os.path.join(S, "comic"), exist_ok=True)
    os.makedirs(os.path.join(S, "chronicles"), exist_ok=True)

    for i, it in enumerate(its):
        open(os.path.join(S, "comic/issue-%02d.html" % it["number"]), "w", encoding="utf-8").write(
            _tpl.comic_page(it, its[i - 1] if i else None,
                            its[i + 1] if i + 1 < len(its) else None, inline))
    for i, e in enumerate(es):
        open(os.path.join(S, "chronicles/%03d.html" % e["n"]), "w", encoding="utf-8").write(
            _tpl.chron_page(e, es[i - 1] if i else None,
                            es[i + 1] if i + 1 < len(es) else None, md(e["body"])))

    open(os.path.join(S, "comic/index.html"), "w", encoding="utf-8").write(_idx.comic_index(its))
    open(os.path.join(S, "chronicles/index.html"), "w", encoding="utf-8").write(_idx.chron_index(es))
    open(os.path.join(S, "index.html"), "w", encoding="utf-8").write(_idx.hub(its, es))
    write_data(its, es)
    print("wrote %d comic readers, %d chronicle readers" % (len(its), len(es)))


if __name__ == "__main__":
    main()
