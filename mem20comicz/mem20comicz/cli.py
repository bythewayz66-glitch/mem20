"""CLI entry point for mem20comicz."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mem20comicz.pipeline import ComicPipeline


def main():
    p = argparse.ArgumentParser()
    p.add_argument("script", help="shooting script markdown")
    p.add_argument("--adapter", default="openai")
    p.add_argument("--out", default="./pages")
    args = p.parse_args()
    pipe = ComicPipeline(adapter_name=args.adapter, out_dir=args.out)
    beats = pipe.parse_beats(args.script)
    print(f"ingested {len(beats)} beats")
    for b in beats:
        print(b["page"], "-", b["title"])


if __name__ == "__main__":
    main()