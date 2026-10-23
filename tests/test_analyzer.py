"""Cross-checks against the analysis script provided with the subject.

``maze_analyzer.py`` is the reference implementation of the rules the
project is graded on, so it is the strongest available oracle: these tests
generate mazes, write them, and require the analyzer to reach the expected
verdict -- including the ``--max-dead-ends 0`` bonus threshold.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Optional

import pytest

from amazeing.output import write_maze
from mazegen import MazeGenerator

_ANALYZER = Path(__file__).resolve().parent.parent / "maze_analyzer.py"


def _load_analyzer() -> Optional[ModuleType]:
    """Import ``maze_analyzer.py`` from the repository root, if present."""
    if not _ANALYZER.is_file():
        return None
    spec = importlib.util.spec_from_file_location("maze_analyzer", _ANALYZER)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    # The analyzer defines dataclasses, which look their own module up in
    # ``sys.modules`` while being built: register it before executing.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


analyzer = _load_analyzer()

pytestmark = pytest.mark.skipif(
    analyzer is None,
    reason="maze_analyzer.py is not present at the repository root",
)

MIN_LOOPS = 2
NO_DEAD_END = 0


def verdict_of(
    tmp_path: Path,
    width: int,
    height: int,
    perfect: bool,
    seed: int,
) -> str:
    """Generate a maze, write it, and return the analyzer verdict."""
    assert analyzer is not None
    generator = MazeGenerator(
        width,
        height,
        (0, 0),
        (width - 1, height - 1),
        perfect=perfect,
        seed=seed,
    ).generate()
    path = tmp_path / "maze.txt"
    write_maze(str(path), generator)
    report = analyzer.analyze(analyzer.Maze.from_file(str(path)))
    return str(analyzer.verdict(report, MIN_LOOPS, NO_DEAD_END))


@pytest.mark.parametrize("seed", [1, 3, 42])
def test_perfect_mazes_are_recognised_as_perfect(
    tmp_path: Path, seed: int
) -> None:
    """``PERFECT=True`` must be seen as a single-path maze."""
    assert verdict_of(
        tmp_path, 25, 17, True, seed
    ).startswith("PERFECT maze")


@pytest.mark.parametrize("seed", [1, 3, 42])
def test_boards_are_pac_man_usable_with_no_dead_end(
    tmp_path: Path, seed: int
) -> None:
    """``PERFECT=False`` gives a playable board without dead-ends."""
    verdict = verdict_of(tmp_path, 25, 17, False, seed)
    assert verdict.startswith("Pac-Man-USABLE")
    assert "bonus-grade" in verdict


@pytest.mark.parametrize(
    "width, height",
    [(9, 7), (12, 9), (21, 15), (31, 21), (40, 12), (12, 40)],
)
def test_many_sizes_stay_pac_man_usable(
    tmp_path: Path, width: int, height: int
) -> None:
    """Boards of very different shapes all stay playable."""
    verdict = verdict_of(tmp_path, width, height, False, width * height)
    assert verdict.startswith("Pac-Man-USABLE")
    assert "bonus-grade" in verdict


@pytest.mark.parametrize("seed", range(12))
def test_random_seeds_stay_valid(tmp_path: Path, seed: int) -> None:
    """Whatever the seed, the analyzer never reports an invalid maze."""
    for perfect in (True, False):
        verdict = verdict_of(tmp_path, 23, 15, perfect, seed)
        assert not verdict.startswith("INCOHERENT")
        assert not verdict.startswith("NOT fully connected")
        assert not verdict.startswith("DEGENERATE")
        assert not verdict.startswith("Not Pac-Man-ready")


def test_walls_are_never_incoherent(tmp_path: Path) -> None:
    """The analyzer finds no mismatching shared wall."""
    assert analyzer is not None
    generator = MazeGenerator(
        25, 17, (0, 0), (24, 16), perfect=False, seed=77
    ).generate()
    path = tmp_path / "maze.txt"
    write_maze(str(path), generator)
    maze = analyzer.Maze.from_file(str(path))
    assert maze.incoherent_cells() == ()
    assert maze.entry == (0, 0)
    assert maze.exit == (16, 24)
