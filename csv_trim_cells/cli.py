"""Trim whitespace in CSV cells.

Removes leading and/or trailing whitespace from every cell of a CSV.
Also supports collapsing internal runs of whitespace and optionally
dropping rows that become entirely empty.

Exit codes:
    0 - success (or --check with no trimming needed)
    1 - I/O or CLI usage error
    2 - --check and at least one cell would be trimmed, or a
        --require constraint failed
"""
import argparse
import csv
import json
import re
import sys


def _transform_cell(cell, side, collapse):
    original = cell
    if side in ("both", "left"):
        cell = cell.lstrip()
    if side in ("both", "right"):
        cell = cell.rstrip()
    if collapse:
        cell = re.sub(r"\s+", " ", cell)
    return cell, original != cell


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="csv-trim-cells",
        description="Trim whitespace in CSV cells (header aware).",
    )
    p.add_argument("file", nargs="?", default="-",
                   help="CSV file, or '-' for stdin (default)")
    p.add_argument("--delimiter", default=",",
                   help="column delimiter (default: ','); use '\\t' for tab")
    p.add_argument("--no-header", action="store_true",
                   help="no header row; all rows are data")
    p.add_argument("--trim-header", action="store_true",
                   help="also trim cells of the header row")
    p.add_argument("--side", choices=["both", "left", "right"], default="both",
                   help="which side to trim (default: both)")
    p.add_argument("--collapse", action="store_true",
                   help="collapse internal whitespace runs to a single space")
    p.add_argument("--columns", default=None,
                   help="only trim these columns (names or 1-based indices, "
                        "comma-separated); default: all columns")
    p.add_argument("--drop-empty-rows", action="store_true",
                   help="drop data rows that are entirely empty after trimming")
    p.add_argument("--check", action="store_true",
                   help="do not write output; exit 2 when trimming would "
                        "change something (CI mode)")
    p.add_argument("--require-trimmed-max", type=int, default=None,
                   help="fail (exit 2) if more than MAX cells would be trimmed")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="suppress summary on stderr")
    p.add_argument("--json", action="store_true", help="JSON report output")
    args = p.parse_args(argv)

    delimiter = args.delimiter.encode().decode("unicode_escape")
    if len(delimiter) != 1:
        sys.stderr.write("error: delimiter must be a single character\n")
        return 1

    try:
        if args.file == "-":
            rows = list(csv.reader(sys.stdin, delimiter=delimiter))
        else:
            with open(args.file, "r", encoding="utf-8", newline="") as fh:
                rows = list(csv.reader(fh, delimiter=delimiter))
    except OSError as exc:
        sys.stderr.write(f"error: cannot read {args.file}: {exc}\n")
        return 1

    header = None
    data_start = 0
    if rows and not args.no_header:
        header = rows[0]
        data_start = 1

    col_filter = None
    if args.columns:
        col_filter = set()
        for part in args.columns.split(","):
            part = part.strip()
            if not part:
                continue
            if part.lstrip("-").isdigit():
                idx = int(part)
                if idx < 1:
                    sys.stderr.write(f"error: column index must be >= 1: {part}\n")
                    return 1
                col_filter.add(idx - 1)
            else:
                if header is None:
                    sys.stderr.write(
                        f"error: column name '{part}' requires a header row\n")
                    return 1
                if part not in header:
                    sys.stderr.write(f"error: unknown column name: {part}\n")
                    return 1
                col_filter.add(header.index(part))

    trimmed_cells = 0
    dropped_rows = 0
    out_rows = []
    for i, row in enumerate(rows):
        is_header = header is not None and i == 0
        if is_header and not args.trim_header:
            out_rows.append(row)
            continue
        new_row = []
        for j, cell in enumerate(row):
            if col_filter is not None and j not in col_filter:
                new_row.append(cell)
                continue
            new_cell, changed = _transform_cell(cell, args.side, args.collapse)
            if changed:
                trimmed_cells += 1
            new_row.append(new_cell)
        if args.drop_empty_rows and all(c == "" for c in new_row):
            dropped_rows += 1
            continue
        out_rows.append(new_row)

    failed = None
    if args.require_trimmed_max is not None and trimmed_cells > args.require_trimmed_max:
        failed = (f"trimmed cells ({trimmed_cells}) exceed maximum "
                  f"{args.require_trimmed_max}")

    if args.json:
        json.dump({
            "file": args.file,
            "rows_in": len(rows),
            "rows_out": len(out_rows),
            "trimmed_cells": trimmed_cells,
            "dropped_rows": dropped_rows,
            "require_trimmed_max": args.require_trimmed_max,
            "check": failed is None,
        }, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    elif not args.check:
        writer = csv.writer(sys.stdout, delimiter=delimiter, lineterminator="\n")
        writer.writerows(out_rows)

    if failed:
        sys.stderr.write(f"error: {failed}\n")
        return 2
    if args.check and trimmed_cells:
        if not args.quiet:
            sys.stderr.write(
                f"check: {trimmed_cells} cell(s) would be trimmed\n")
        return 2
    if not args.quiet and not args.json:
        sys.stderr.write(f"ok: {trimmed_cells} cell(s) trimmed, "
                         f"{dropped_rows} empty row(s) dropped\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
