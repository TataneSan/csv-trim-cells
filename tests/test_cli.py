import io
import json
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr

from csv_trim_cells.cli import main


def run(argv, stdin_text=""):
    out = io.StringIO()
    err = io.StringIO()
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin_text)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
    finally:
        sys.stdin = old_stdin
    return code, out.getvalue(), err.getvalue()


CSV = "name,city\n  Alice , Paris \nBob,Lyon  \n"


class TestCsvTrimCells(unittest.TestCase):
    def test_basic_trim(self):
        code, out, _ = run(["-"], CSV)
        self.assertEqual(code, 0)
        self.assertEqual(out, "name,city\nAlice,Paris\nBob,Lyon\n")

    def test_column_target(self):
        code, out, _ = run(["--columns", "2", "-"], CSV)
        self.assertEqual(code, 0)
        self.assertEqual(out, "name,city\n  Alice ,Paris\nBob,Lyon\n")

    def test_trim_header(self):
        code, out, _ = run(["--trim-header", "-"], " a ,b\n 1 ,2\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "a,b\n1,2\n")

    def test_report(self):
        code, out, _ = run(["--report", "-"], CSV)
        self.assertEqual(code, 0)
        self.assertIn("cells changed: 3", out)

    def test_json(self):
        code, out, _ = run(["--report", "--json", "-"], CSV)
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["cells_changed"], 3)
        self.assertEqual(report["rows_changed"], 2)
        self.assertTrue(report["checks"]["ok"])

    def test_check_fail(self):
        code, _, err = run(["--report", "--check", "1", "-"], CSV)
        self.assertEqual(code, 2)
        self.assertIn("CHECK FAILED", err)

    def test_check_pass(self):
        code, _, _ = run(["--report", "--check", "10", "-"], CSV)
        self.assertEqual(code, 0)

    def test_no_header(self):
        code, out, _ = run(["--no-header", "-"], " a ,b\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "a,b\n")

    def test_quoted_cells(self):
        # single row treated as header by default -> preserved
        code, out, _ = run(["-"], '"  spaced  ",x\n" a "," b "\n')
        self.assertEqual(code, 0)
        self.assertEqual(out, "  spaced  ,x\na,b\n")


if __name__ == "__main__":
    unittest.main()
