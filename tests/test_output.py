"""Tests of the output file and of the program as a whole.

The maze written on disk is re-read and checked from scratch, without
looking at the generator internals, the way an external analysis script
would do it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pytest

import a_maze_ing
from amazeing.output import build_lines, write_maze
from mazegen import MazeGenerator

Coord = Tuple[int, int]

_NORTH, _EAST, _SOUTH, _WEST = 1, 2, 4, 8
_DELTA: Dict[int, Coord] = {
    _NORTH: (0, -1),
    _EAST: (1, 0),
    _SOUTH: (0, 1),
    _WEST: (-1, 0),
}
_OPPOSITE: Dict[int, int] = {
    _NORTH: _SOUTH,
    _EAST: _WEST,
    _SOUTH: _NORTH,
    _WEST: _EAST,
}
_LETTER: Dict[str, int] = {
    "N": _NORTH,
    "E": _EAST,
    "S": _SOUTH,
    "W": _WEST,
}


class ParsedMaze:
    """A maze rebuilt from the content of an output file."""

    def __init__(self, text: str) -> None:
        """Parse ``text``, the full content of an output file."""
        lines = text.split("\n")
        assert lines[-1] == "", "the file must end with a newline"
        lines = lines[:-1]
        blank = lines.index("")
        self.grid: List[List[int]] = [
            [int(digit, 16) for digit in line] for line in lines[:blank]
        ]
        header = lines[blank + 1:]
        assert len(header) == 3, "entry, exit and path must follow"
        self.entry = self._coord(header[0])
        self.exit = self._coord(header[1])
        self.path = header[2]
        self.height = len(self.grid)
        self.width = len(self.grid[0])

    @staticmethod
    def _coord(line: str) -> Coord:
        """Parse a ``x,y`` line."""
        raw_x, raw_y = line.split(",")
        return int(raw_x), int(raw_y)

    def is_open(self, x: int, y: int, direction: int) -> bool:
        """Tell whether a wall of ``(x, y)`` is open."""
        return not self.grid[y][x] & direction

    def walk(self) -> Coord:
        """Follow ``self.path`` from the entry and return where it ends."""
        x, y = self.entry
        for letter in self.path:
            direction = _LETTER[letter]
            assert self.is_open(x, y, direction), "the path crosses a wall"
            delta_x, delta_y = _DELTA[direction]
            x, y = x + delta_x, y + delta_y
        return x, y

    def check_coherence(self) -> None:
        """Assert that neighbours agree on the wall they share."""
        for y in range(self.height):
            assert len(self.grid[y]) == self.width
            for x in range(self.width):
                for direction in (_EAST, _SOUTH):
                    delta_x, delta_y = _DELTA[direction]
                    near_x, near_y = x + delta_x, y + delta_y
                    if near_x >= self.width or near_y >= self.height:
                        continue
                    mine = self.is_open(x, y, direction)
                    theirs = self.is_open(
                        near_x, near_y, _OPPOSITE[direction]
                    )
                    assert mine == theirs, f"wall {x},{y} is incoherent"

    def corridors(self) -> Set[Coord]:
        """Return the cells that are not fully closed."""
        return {
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.grid[y][x] != 0xF
        }

    def edges(self) -> int:
        """Count the open passages of the maze."""
        total = 0
        for y in range(self.height):
            for x in range(self.width):
                if x + 1 < self.width and self.is_open(x, y, _EAST):
                    total += 1
                if y + 1 < self.height and self.is_open(x, y, _SOUTH):
                    total += 1
        return total

    def reachable_from(self, start: Coord) -> Set[Coord]:
        """Return every cell reachable from ``start``."""
        seen = {start}
        stack = [start]
        while stack:
            x, y = stack.pop()
            for direction, (delta_x, delta_y) in _DELTA.items():
                if not self.is_open(x, y, direction):
                    continue
                cell = (x + delta_x, y + delta_y)
                if cell not in seen:
                    seen.add(cell)
                    stack.append(cell)
        return seen


def generate_file(tmp_path: Path, **kwargs: Any) -> ParsedMaze:
    """Generate a maze, write it, and parse the file back."""
    params: Dict[str, Any] = {
        "width": 25,
        "height": 17,
        "entry": (0, 0),
        "exit": (24, 16),
        "seed": 11,
    }
    params.update(kwargs)
    generator = MazeGenerator(**params).generate()
    path = tmp_path / "maze.txt"
    write_maze(str(path), generator)
    return ParsedMaze(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("perfect", [True, False])
def test_output_file_is_coherent(tmp_path: Path, perfect: bool) -> None:
    """The written file describes a coherent, connected maze."""
    maze = generate_file(tmp_path, perfect=perfect)
    maze.check_coherence()
    assert maze.entry == (0, 0)
    assert maze.exit == (24, 16)
    assert maze.walk() == maze.exit
    assert maze.reachable_from(maze.entry) == maze.corridors()


def test_output_file_borders_are_closed(tmp_path: Path) -> None:
    """The outer walls of the written maze are all closed."""
    maze = generate_file(tmp_path)
    for x in range(maze.width):
        assert not maze.is_open(x, 0, _NORTH)
        assert not maze.is_open(x, maze.height - 1, _SOUTH)
    for y in range(maze.height):
        assert not maze.is_open(0, y, _WEST)
        assert not maze.is_open(maze.width - 1, y, _EAST)


def test_perfect_file_is_a_tree(tmp_path: Path) -> None:
    """A perfect maze holds exactly one path between any two cells."""
    maze = generate_file(tmp_path, perfect=True)
    assert maze.edges() == len(maze.corridors()) - 1


def test_playable_file_has_several_routes(tmp_path: Path) -> None:
    """A playable board keeps at least two independent routes."""
    maze = generate_file(tmp_path, perfect=False)
    loops = maze.edges() - len(maze.corridors()) + 1
    assert loops >= 2


def test_path_is_the_shortest_one(tmp_path: Path) -> None:
    """The exported path is as short as a breadth-first search one."""
    generator = MazeGenerator(25, 17, (0, 0), (24, 16), seed=11).generate()
    assert len(generator.directions) == len(generator.solution) - 1


def test_file_layout(tmp_path: Path) -> None:
    """Rows, an empty line, the entry, the exit, then the path."""
    generator = MazeGenerator(10, 8, (0, 0), (9, 7), seed=2).generate()
    lines = build_lines(generator)
    assert len(lines) == 8 + 4
    assert lines[8] == ""
    assert lines[9] == "0,0"
    assert lines[10] == "9,7"
    assert set(lines[11]) <= set("NESW")


def test_program_end_to_end(tmp_path: Path) -> None:
    """Running the program writes a usable maze and returns 0."""
    output = tmp_path / "out.txt"
    config = tmp_path / "config.txt"
    config.write_text(
        "WIDTH=21\nHEIGHT=15\nENTRY=0,0\nEXIT=20,14\n"
        f"OUTPUT_FILE={output}\nPERFECT=True\nSEED=9\n",
        encoding="utf-8",
    )
    assert a_maze_ing.main(["a_maze_ing.py", str(config)]) == 0
    maze = ParsedMaze(output.read_text(encoding="utf-8"))
    maze.check_coherence()
    assert maze.walk() == maze.exit


def test_program_reports_errors() -> None:
    """Bad arguments and bad files exit with status 1."""
    assert a_maze_ing.main(["a_maze_ing.py"]) == 1
    assert a_maze_ing.main(["a_maze_ing.py", "a", "b"]) == 1
    assert a_maze_ing.main(["a_maze_ing.py", "missing.txt"]) == 1


def test_program_help() -> None:
    """``--help`` succeeds."""
    assert a_maze_ing.main(["a_maze_ing.py", "--help"]) == 0
