"""Module entry point for ``python -m csv_trim_cells``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
