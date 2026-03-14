#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


CHECK_RE = re.compile(r"^\s*[-*]\s*\[(?P<done>[ xX])\]\s*(?P<text>.+?)\s*$")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert markdown checklist items into CSV for Codex batch fan-out.")
    parser.add_argument("--input", required=True, help="Input markdown file")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output)

    rows = []
    for idx, line in enumerate(inp.read_text(encoding="utf-8").splitlines(), start=1):
        match = CHECK_RE.match(line)
        if not match:
            continue
        rows.append({
            "id": str(idx),
            "done": "true" if match.group("done").lower() == "x" else "false",
            "title": match.group("text").strip(),
        })

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "done", "title"])
        writer.writeheader()
        writer.writerows(rows)

    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
