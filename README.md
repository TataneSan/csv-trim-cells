# csv-trim-cells

Strip leading and trailing whitespace from cells of a CSV file, with
per-column targeting and CI-friendly threshold checks.

By default every data cell is trimmed; the header row is preserved unless
`--trim-header` is passed. Trimming happens on parsed values, so quoted
fields are unquoted/requoted cleanly by the CSV writer.

## Installation

```sh
pip install .
```

Or run directly:

```sh
python -m csv_trim_cells --help
```

## Usage

```
csv-trim-cells [INPUT] [options]
```

`INPUT` is a CSV file path. When omitted or `-`, input is read from stdin.

### Options

| Option | Description |
| --- | --- |
| `--columns LIST` | Comma-separated 1-based column indexes to trim (default: all). |
| `--no-header` | Treat the first row as data. |
| `--trim-header` | Also trim the header row. |
| `--delimiter CHAR` | Field delimiter (default `,`). Use `\t` for tab. |
| `--report` | Emit only the change report, not the trimmed CSV. |
| `--check MAX_CHANGED` | Exit 2 if more than MAX_CHANGED cells were trimmed. |
| `--json` | Emit the report as JSON. |

### Exit codes

- `0` — success (or all checks passed)
- `1` — CLI / I/O / parse error
- `2` — a `--check` threshold was exceeded

## Examples

Trim whitespace from all cells:

```sh
$ printf 'name,city\n  Alice , Paris \nBob,Lyon  \n' | csv-trim-cells -
name,city
Alice,Paris
Bob,Lyon
```

Trim only the second column:

```sh
$ csv-trim-cells data.csv --columns 2
```

Report only, useful in scripts:

```sh
$ csv-trim-cells data.csv --report --json | jq '.cells_changed'
```

CI guard — fail if anyone committed sloppy whitespace:

```sh
$ csv-trim-cells data.csv --check 0 || echo "whitespace found in CSV"
```

## License

MIT
