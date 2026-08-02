"""csv-trim-cells: strip leading/trailing whitespace from CSV cells.

By default all whitespace (spaces, tabs) at the start and end of every
data cell is removed. Header trimming is optional. Fields that were
quoted in the input keep their inner content; trimming happens on the
parsed value.

Exit codes:
    0 - success (or check passed)
    1 - CLI / I/O error
    2 - check mode: threshold not satisfied
"""

import argparse
import csv
import io
import json
import sys


def build_parser():
    p = argparse.ArgumentParser(
        prog="csv-trim-cells",
        description=(
            "Strip leading and trailing whitespace from cells of a CSV. "
            "Reads a file or stdin when the path is omitted or '-'."
        ),
    )
    p.add_argument("input", nargs="?", default="-",
                   help="CSV input path (default: stdin; '-' = stdin)")
    p.add_argument("--columns", default=None,
                   help="Comma-separated 1-based column indexes to trim "
                        "(default: all columns)")
    p.add_argument("--no-header", action="store_true",
                   help="Treat the first row as data (no header row)")
    p.add_argument("--trim-header", action="store_true",
                   help="Also trim the header row")
    p.add_argument("--delimiter", default=",",
                   help="Field delimiter (default: ','). Use '\\t' for tab.")
    p.add_argument("--report", action="store_true",
                   help="Do not emit the trimmed CSV; emit only the report "
                        "of how many cells were changed")
    p.add_argument("--check", metavar="MAX_CHANGED", type=int, default=None,
                   help="Exit 2 if the number of trimmed cells exceeds "
                        "MAX_CHANGED")
    p.add_argument("--json", action="store_true",
                   help="Emit the report as JSON (default: human-readable text)")
    return p


def open_input(path):
    if path == "-":
        return sys.stdin
    return open(path, "r", newline="", encoding="utf-8")


def parse_columns(spec):
    cols = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            n = int(part)
        except ValueError:
            return None
        if n < 1:
            return None
        cols.add(n - 1)
    return cols


def main(argv=None):
    args = build_parser().parse_args(argv)
    delim = args.delimiter
    if delim == "\\t":
        delim = "\t"
    if len(delim) != 1:
        print("error: --delimiter must be a single character", file=sys.stderr)
        return 1

    target_cols = None
    if args.columns:
        target_cols = parse_columns(args.columns)
        if target_cols is None:
            print("error: --columns must be comma-separated positive integers",
                  file=sys.stderr)
            return 1

    try:
        fh = open_input(args.input)
    except OSError as exc:
        print("error: cannot open input: %s" % exc, file=sys.stderr)
        return 1

    rows_read = 0
    cells_changed = 0
    rows_changed = 0
    out_buf = io.StringIO()
    writer = csv.writer(out_buf, delimiter=delim, lineterminator="\n")

    close = fh is not sys.stdin
    try:
        reader = csv.reader(fh, delimiter=delim)
        first = True
        for row in reader:
            is_header_row = first and not args.no_header
            first = False
            if is_header_row and not args.trim_header:
                writer.writerow(row)
                continue
            rows_read += 1
            row_changed = False
            new_row = []
            for i, cell in enumerate(row):
                if target_cols is not None and i not in target_cols:
                    new_row.append(cell)
                    continue
                trimmed = cell.strip()
                if trimmed != cell:
                    cells_changed += 1
                    row_changed = True
                new_row.append(trimmed)
            if row_changed:
                rows_changed += 1
            writer.writerow(new_row)
    except csv.Error as exc:
        print("error: CSV parse error: %s" % exc, file=sys.stderr)
        return 1
    finally:
        if close:
            fh.close()

    failures = []
    if args.check is not None and cells_changed > args.check:
        failures.append("cells_changed %d > max %d" % (cells_changed, args.check))

    report = {
        "input": args.input,
        "rows_read": rows_read,
        "rows_changed": rows_changed,
        "cells_changed": cells_changed,
        "columns": sorted(c + 1 for c in target_cols) if target_cols else "all",
        "checks": {"ok": not failures, "failures": failures},
    }

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        if not args.report:
            sys.stdout.write(out_buf.getvalue())
    elif args.report:
        print("input:         %s" % args.input)
        print("rows read:     %d" % rows_read)
        print("rows changed:  %d" % rows_changed)
        print("cells changed: %d" % cells_changed)
        if failures:
            for f in failures:
                print("CHECK FAILED: %s" % f, file=sys.stderr)
    else:
        sys.stdout.write(out_buf.getvalue())
        if failures:
            for f in failures:
                print("CHECK FAILED: %s" % f, file=sys.stderr)

    return 2 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
