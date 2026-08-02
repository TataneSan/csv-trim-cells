import io
import sys
import unittest

from csv_trim_cells.cli import clean_cell, main, process_rows


class CleanCellTest(unittest.TestCase):
    def test_strip(self):
        self.assertEqual(clean_cell("  hello  "), ("hello", True))
        self.assertEqual(clean_cell("hello"), ("hello", False))

    def test_collapse(self):
        self.assertEqual(clean_cell("a   b\t c", collapse=True), ("a b c", True))
        self.assertEqual(clean_cell("a b", collapse=True), ("a b", False))
        # without collapse, internal runs are kept
        self.assertEqual(clean_cell("a   b"), ("a   b", False))


class ProcessRowsTest(unittest.TestCase):
    def test_per_column_counts(self):
        rows = [["name", "city"], [" Alice ", " Paris "], ["Bob", "Lyon"]]
        cleaned, per_col, total = process_rows(rows)
        self.assertEqual(cleaned[1], ["Alice", "Paris"])
        self.assertEqual(total, 2)
        self.assertEqual(per_col, {"name": 1, "city": 1})


class MainTest(unittest.TestCase):
    def _run(self, text, argv):
        old_in, old_out = sys.stdin, sys.stdout
        sys.stdin = io.StringIO(text)
        sys.stdout = io.StringIO()
        try:
            rc = main(argv)
            out = sys.stdout.getvalue()
        finally:
            sys.stdin, sys.stdout = old_in, old_out
        return rc, out

    def test_trims_and_writes(self):
        rc, out = self._run("name, city \n Alice , Paris \n", ["-q", "-"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "name,city\nAlice,Paris\n")

    def test_check_exit_codes(self):
        dirty = "name,age\n Alice , 42 \n"
        clean = "name,age\nAlice,42\n"
        self.assertEqual(self._run(dirty, ["--check", "-q", "-"])[0], 2)
        self.assertEqual(self._run(clean, ["--check", "-q", "-"])[0], 0)

    def test_check_does_not_rewrite(self):
        rc, out = self._run("a, b\n1, 2\n", ["--check", "--json", "-"])
        self.assertEqual(rc, 2)
        self.assertNotIn("a,b\n1,2\n", out)

    def test_json_report(self):
        rc, out = self._run("name, city \n Alice , Paris \n",
                            ["--json", "--check", "-"])
        self.assertEqual(rc, 2)
        import json
        report = json.loads(out)
        self.assertEqual(report["changed_cells"], 3)
        self.assertEqual(report["columns"], {"name": 1, "city": 2})

    def test_semicolon_delimiter(self):
        rc, out = self._run("a; b \n 1 ; 2 \n", ["-q", "-"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "a;b\n1;2\n")

    def test_collapse_flag(self):
        rc, out = self._run("note\na    b\n", ["--collapse", "-q", "-"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "note\na b\n")

    def test_empty_input(self):
        self.assertEqual(self._run("", ["-q", "-"])[0], 0)
        self.assertEqual(self._run("  \n", ["--check", "-q", "-"])[0], 0)

    def test_missing_file(self):
        self.assertEqual(main(["-q", "/nonexistent/nope.csv"]), 1)


if __name__ == "__main__":
    unittest.main()
