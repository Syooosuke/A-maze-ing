"""Application layer of the A-Maze-ing project.

The reusable maze generation logic lives in the standalone :mod:`mazegen`
module.  This package only holds what is specific to the command line
program: configuration parsing, output file writing, terminal rendering,
the interactive menu and the optional MiniLibX window.
"""

from __future__ import annotations

__all__ = ["config", "mlxview", "output", "render", "ui"]
