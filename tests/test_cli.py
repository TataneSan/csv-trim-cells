import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

from csv_trim_cells.cli import main, resolve_columns


class ResolveTests(unittest.TestCase):
    def test_all(self):
        self.assertIsNone(resolve_columns(["a", "b"], None))

    def test_name(self):
        self.assertEqual(resolve_columns(["a", "b"], ["b"]), [1])

    def test_padded_header(self):
        self.assertEqual(resolve_columns([" a ", "b"], ["a"]), [0])

    def test_index(self):
        self.assertEqual(resolve_columns(["a", "b"], ["1"]), [1])

    def test_missing(self):
        with self.assertRaises(ValueError):
            resolve_columns(["a"], ["z"])


class CliTests(unittest.TestCase):
    def run_cli(self, argv, stdin_text=""):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(stdin_text)), \
                redirect_stdout(out), redirect_stderr(err):
            rc = main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_trim_all(self):
        rc, out, _ = self.run_cli(["-"], " name , age \n alice , 30 \n")
        self.assertEqual(rc, 0)
        self.assertIn("name,age", out)
        self.assertIn("alice,30", out)

    def test_column(self):
        rc, out, _ = self.run_cli(["-", "-c", "name"], " name ,ok\n alice ,x\n")
        self.assertIn("name,ok", out)
        self.assertIn("alice,x", out)

    def test_missing_column(self):
        rc, _, err = self.run_cli(["-", "-c", "z"], "a,b\n1,2\n")
        self.assertEqual(rc, 1)
        self.assertIn("z", err)

    def test_check_dirty(self):
        rc, out, _ = self.run_cli(["-", "--check"], "a,b\n x ,y\n")
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")

    def test_check_clean(self):
        rc, _, _ = self.run_cli(["-", "--check"], "a,b\nx,y\n")
        self.assertEqual(rc, 0)

    def test_json(self):
        rc, out, _ = self.run_cli(["-", "--json"], "a,b\n x , y \n")
        report = json.loads(out)
        self.assertEqual(report["trimmed_cells"], 2)

    def test_missing_file(self):
        rc, _, _ = self.run_cli(["/no/such/file"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
