"""``python3 -m rgengy`` - the command-line entry point.

Kept trivial on purpose: the real work, argument parsing and exit codes live in
:mod:`rgengy.cli`, so there is exactly one implementation of the CLI and this
file only makes it runnable as a module.
"""

from __future__ import annotations

import sys

from rgengy.cli import main

if __name__ == "__main__":
    sys.exit(main())
