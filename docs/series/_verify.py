#!/usr/bin/env python3
"""Assert the generated series corpus is complete and self-consistent.

Run after _build.py. Exits non-zero if the index pages, the JSON feeds and the
reader pages disagree about what has been published.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    comic_dir = os.path.join(HERE, "comic")
    chron_dir = os.path.join(HERE, "chronicles")

    comic_pages = sorted(
        f for f in os.listdir(comic_dir) if re.fullmatch(r"issue-\d+\.html", f)
    )
    chron_pages = sorted(
        f for f in os.listdir(chron_dir) if re.fullmatch(r"\d{3}\.html", f)
    )

    comic_feed = json.load(open(os.path.join(HERE, "data/comic-issues.json")))
    chron_feed = json.load(open(os.path.join(HERE, "data/chronicles.json")))

    issues = comic_feed["issues"]
    entries = chron_feed["entries"]

    print("comic reader pages:      %d" % len(comic_pages))
    print("comic-issues.json:       %d" % len(issues))
    print("chronicle reader pages:  %d" % len(chron_pages))
    print("chronicles.json:         %d" % len(entries))

    errors = []

    if len(comic_pages) != len(issues):
        errors.append("comic page count %d != feed count %d" % (len(comic_pages), len(issues)))
    if len(chron_pages) != len(entries):
        errors.append("chronicle page count %d != feed count %d" % (len(chron_pages), len(entries)))

    for it in issues:
        want = "issue-%02d.html" % it["number"]
        if want not in comic_pages:
            errors.append("missing comic page %s" % want)
        if it.get("state") != "ready":
            errors.append("issue %s is not marked ready" % it["number"])
        if not it.get("pdf_url"):
            errors.append("issue %s has no pdf_url" % it["number"])

    for e in entries:
        want = "%03d.html" % e["installment"]
        if want not in chron_pages:
            errors.append("missing chronicle page %s" % want)
        if e.get("origin") not in ("grounded", "simulated"):
            errors.append("installment %s has no origin tag" % e["installment"])

    comic_index = open(os.path.join(comic_dir, "index.html"), encoding="utf-8").read()
    for it in issues:
        if "issue-%02d.html" % it["number"] not in comic_index:
            errors.append("comic index does not link issue %02d" % it["number"])

    chron_index = open(os.path.join(chron_dir, "index.html"), encoding="utf-8").read()
    for e in entries:
        if "%03d.html" % e["installment"] not in chron_index:
            errors.append("chronicle index does not link installment %03d" % e["installment"])

    feed = open(os.path.join(chron_dir, "feed.xml"), encoding="utf-8").read()
    items = feed.count("<item>")
    if items != len(entries):
        errors.append("feed has %d items, expected %d" % (items, len(entries)))

    for name in comic_pages:
        body = open(os.path.join(comic_dir, name), encoding="utf-8").read()
        if len(body) < 2000:
            errors.append("%s looks empty (%d bytes)" % (name, len(body)))
        if "../series.css" not in body:
            errors.append("%s does not load the shared series.css" % name)
        if "../analytics.js" not in body:
            errors.append("%s does not load analytics.js" % name)

    for name in chron_pages:
        body = open(os.path.join(chron_dir, name), encoding="utf-8").read()
        if len(body) < 2000:
            errors.append("%s looks empty (%d bytes)" % (name, len(body)))
        if "../series.css" not in body:
            errors.append("%s does not load the shared series.css" % name)
        if "../analytics.js" not in body:
            errors.append("%s does not load analytics.js" % name)

    if errors:
        print("\nFAILED:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    print("\nOK: pages, feeds and indexes agree.")


if __name__ == "__main__":
    main()
