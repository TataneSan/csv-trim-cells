"""Trim leading/trailing whitespace from every cell of a CSV file.

Reads a CSV file (or stdin), sniffs its delimiter, and rewrites it with
leading/trailing whitespace removed from each cell. Optionally collapses
internal whitespace runs to a single space. A --check lint mode reports
dirty cells without rewriting, and --json emits a machine-readable report
of modified cells grouped by column.

Exit codes:
    0 - success (file written, or --check found nothing to trim)
    1 - I/O or CLI error
    2 - --check was given and at least one cell had extra whitespace
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys

_WS_RUN = re.compile(r"\s+")


def sniff_dialect(sample):
    """Sniff a CSV dialect from a sample; fall back to comma on failure.

    skipinitialspace is forced off so raw cell whitespace is visible to
    the trimming logic instead of being eaten by the parser.
    """
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel()
    dialect.skipinitialspace = False
    return dialect


def clean_cell(value, collapse=False):
    """Return (cleaned_value, changed) for a single cell."""
    cleaned = value.strip()
    if collapse:
        cleaned = _WS_RUN.sub(" ", cleaned)
    return cleaned, cleaned != value


def process_rows(rows, collapse=False):
    """Trim every cell. Return (cleaned_rows, per_column_changed, total_changed)."""
    cleaned_rows = []
    total_changed = 0
    header = rows[0] if rows else []
    names = [name.strip() or f"column_{i + 1}" for i, name in enumerate(header)]
    per_column = {}

    for row in rows:
        new_row = []
        for i, cell in enumerate(row):
            cleaned, changed = clean_cell(cell, collapse)
            if changed:
                total_changed += 1
                name = names[i] if i < len(names) else f"column_{i + 1}"
                per_column[name] = per_column.get(name, 0) + 1
            new_row.append(cleaned)
        cleaned_rows.append(new_row)
    return cleaned_rows, per_column, total_changed


def read_text(file_arg):
    if file_arg in (None, "-"):
        return sys.stdin.read()
    with open(file_arg, "r", encoding="utf-8", errors="replace", newline="") as fh:
        return fh.read()


def build_parser():
    p = argparse.ArgumentParser(
        prog="csv-trim-cells",
        description="Trim leading/trailing whitespace from every CSV cell "
                    "(delimiter auto-detected).",
    )
    p.add_argument("file", nargs="?", default="-",
                   help="Input CSV file (default: stdin, '-' for stdin).")
    p.add_argument("--collapse", action="store_true",
                   help="Also collapse internal whitespace runs to one space.")
    p.add_argument("--check", action="store_true",
                   help="Lint mode: do not rewrite; exit 2 if any cell had "
                        "extra whitespace.")
    p.add_argument("--json", action="store_true",
                   help="Emit a JSON report of modified cells per column.")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="Suppress human-readable output.")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        text = read_text(args.file)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not text.strip():
        if args.json:
            print(json.dumps({"file": args.file, "rows": 0,
                              "changed_cells": 0, "columns": {}}, indent=2,
                             sort_keys=True))
        elif not args.quiet:
            print("Empty input: nothing to trim.")
        return 0

    dialect = sniff_dialect(text[:4096])
    try:
        rows = list(csv.reader(io.StringIO(text), dialect))
    except csv.Error as exc:
        print(f"error: could not parse CSV: {exc}", file=sys.stderr)
        return 1

    cleaned_rows, per_column, total_changed = process_rows(rows, args.collapse)

    report = {
        "file": args.file,
        "rows": len(rows),
        "delimiter": getattr(dialect, "delimiter", ","),
        "collapse": args.collapse,
        "changed_cells": total_changed,
        "columns": dict(sorted(per_column.items())),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.quiet:
        if total_changed:
            print(f"{total_changed} cell(s) trimmed across "
                  f"{len(per_column)} column(s):")
            for name, count in sorted(per_column.items()):
                print(f"  {name}: {count}")
        else:
            print(f"No cell needed trimming ({len(rows)} rows).")

    if args.check:
        return 2 if total_changed else 0

    out = io.StringIO()
    writer = csv.writer(out, dialect=dialect, lineterminator="\n")
    writer.writerows(cleaned_rows)
    sys.stdout.write(out.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main())
