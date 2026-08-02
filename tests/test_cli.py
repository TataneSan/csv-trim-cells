import io
import sys
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from csv_trim_cells.cli import main


def run(argv, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    old = sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
    finally:
        sys.stdin = old
    return code, out.getvalue(), err.getvalue()


class TrimTests(unittest.TestCase):
    def test_trim_both(self):
        code, out, _ = run(["-"], "a,b\n 1 , 2 \n")
        self.assertEqual(code, 0)
        self.assertIn("1,2", out)

    def test_header_preserved(self):
        code, out, _ = run(["-"], " h \n x \n")
        self.assertEqual(" h ", out.splitlines()[0])
        self.assertIn("x", out)

    def test_check_exit2(self):
        code, out, _ = run(["--check", "-"], "a\n b\n")
        self.assertEqual(code, 2)

    def test_check_exit0(self):
        code, out, _ = run(["--check", "-"], "a\nb\n")
        self.assertEqual(code, 0)

    def test_collapse(self):
        code, out, _ = run(["--collapse", "-"], "a,b\n x ,  b \n")
        self.assertIn("x,b", out)

    def test_drop_empty(self):
        code, out, _ = run(["--drop-empty-rows", "-"], "a\n   \n")
        data = [l for l in out.strip().splitlines() if l.strip()]
        self.assertEqual(len(data), 1)

    def test_json(self):
        code, out, _ = run(["--json", "-"], "a\n b \n")
        rep = json.loads(out.strip())
        self.assertEqual(rep["trimmed_cells"], 1)

    def test_require_max_fail(self):
        code, out, _ = run(["--require-trimmed-max", "0", "-"], "a\n b\n")
        self.assertEqual(code, 2)

    def test_columns(self):
        code, out, _ = run(["--no-header", "--columns", "1", "-"],
                           " a , b \n x , y \n")
        lines = out.splitlines()
        self.assertEqual("a, b ", lines[0])
        self.assertEqual("x, y ", lines[1])


if __name__ == "__main__":
    unittest.main()
