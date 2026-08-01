#!/usr/bin/env python3
"""csv-trim-cells - strip surrounding whitespace from CSV cells.

Reads CSV from files or stdin and trims leading/trailing whitespace in
every cell (header included) or only in selected columns --columns.
Useful before diffing or deduplicating exported spreadsheets.

Exit codes:
    0 - success
    1 - CLI or I/O error
    2 - --check mode: at least one cell needed trimming (nothing written)
"""

import argparse
import csv
import io
import json
import sys


def read_source(path):
    if path in (None, "-"):
        return "<stdin>", sys.stdin
    return path, open(path, "r", encoding="utf-8", newline="")


def resolve_columns(header, columns):
    if not columns:
        return None  # all
    stripped = [h.strip() for h in header]
    idxs = []
    for col in columns:
        if col.lstrip("-").isdigit():
            idxs.append(int(col))
        else:
            if col not in stripped:
                raise ValueError("column not found: %s" % col)
            idxs.append(stripped.index(col))
    return idxs


def process(reader, writer, columns):
    header = next(reader, None)
    if header is None:
        return 0
    idxs = resolve_columns(header, columns)
    trimmed = 0

    def clean(row):
        nonlocal trimmed
        for i in range(len(row)):
            if idxs is not None and i not in idxs:
                continue
            stripped = row[i].strip()
            if stripped != row[i]:
                trimmed += 1
                row[i] = stripped
        return row

    writer.writerow(clean(header))
    for row in reader:
        writer.writerow(clean(row))
    return trimmed


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="csv-trim-cells",
        description="Trim leading/trailing whitespace from CSV cells.",
    )
    parser.add_argument(
        "files", nargs="*", metavar="FILE",
        help="CSV files; reads stdin when omitted or '-'",
    )
    parser.add_argument(
        "-c", "--columns", metavar="COL", nargs="+", default=None,
        help="only trim these column names / 0-based indexes",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="exit 2 when any cell needs trimming; no CSV written",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE",
        help="write CSV to FILE instead of stdout (single input only)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="emit a JSON summary report",
    )
    args = parser.parse_args(argv)

    if args.output and len(args.files) != 1:
        print("csv-trim-cells: --output requires exactly one input file",
              file=sys.stderr)
        return 1

    files = args.files or ["-"]
    rc = 0
    results = []
    dirty = False

    if args.check or args.json:
        for path in files:
            try:
                name, fh = read_source(path)
            except OSError as exc:
                print("csv-trim-cells: %s: %s" % (path, exc), file=sys.stderr)
                rc = 1
                continue
            try:
                reader = csv.reader(fh)
                writer = csv.writer(io.StringIO())
                trimmed = process(reader, writer, args.columns)
            except ValueError as exc:
                print("csv-trim-cells: %s: %s" % (path, exc), file=sys.stderr)
                rc = 1
                if path not in (None, "-"):
                    fh.close()
                continue
            if path not in (None, "-"):
                fh.close()
            dirty = dirty or trimmed > 0
            results.append({"file": name, "trimmed_cells": trimmed})
    else:
        out_fh = open(args.output, "w", encoding="utf-8", newline="") \
            if args.output else sys.stdout
        for path in files:
            try:
                name, fh = read_source(path)
            except OSError as exc:
                print("csv-trim-cells: %s: %s" % (path, exc), file=sys.stderr)
                rc = 1
                continue
            try:
                reader = csv.reader(fh)
                writer = csv.writer(out_fh)
                trimmed = process(reader, writer, args.columns)
            except ValueError as exc:
                print("csv-trim-cells: %s: %s" % (path, exc), file=sys.stderr)
                rc = 1
                if path not in (None, "-"):
                    fh.close()
                continue
            if path not in (None, "-"):
                fh.close()
            dirty = dirty or trimmed > 0
            results.append({"file": name, "trimmed_cells": trimmed})
        if args.output:
            out_fh.close()

    if args.json:
        payload = results[0] if len(results) == 1 else results
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")

    if args.check and rc == 0:
        return 2 if dirty else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
