"""Terminal rendering of a maze, with ANSI colours."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import groupby
from typing import Dict, List, Set, Tuple

from mazegen import EAST, NORTH, SOUTH, WEST, Coord, MazeGenerator

_RESET = "\x1b[0m"


class Token(Enum):
    """What a half-cell of the rendered canvas stands for."""

    VOID = "void"
    WALL = "wall"
    PATTERN = "pattern"
    PATH = "path"
    ENTRY = "entry"
    EXIT = "exit"


@dataclass(frozen=True)
class Theme:
    """A named set of 256-colour ANSI codes.

    Attributes:
        name: Human readable name, shown in the interactive menu.
        wall: Colour of the maze walls.
        pattern: Colour of the "42" pattern.
        path: Colour of the shortest path.
        entry: Colour of the entry cell.
        exit: Colour of the exit cell.
    """

    name: str
    wall: int
    pattern: int
    path: int
    entry: int
    exit: int


THEMES: Tuple[Theme, ...] = (
    Theme("classic", wall=250, pattern=189, path=51, entry=201, exit=196),
    Theme("amber", wall=214, pattern=229, path=45, entry=201, exit=196),
    Theme("emerald", wall=41, pattern=194, path=105, entry=213, exit=202),
    Theme("ocean", wall=39, pattern=195, path=226, entry=201, exit=196),
    Theme("mono", wall=244, pattern=255, path=231, entry=231, exit=231),
)

_ASCII: Dict[Token, str] = {
    Token.VOID: "  ",
    Token.WALL: "##",
    Token.PATTERN: "%%",
    Token.PATH: "..",
    Token.ENTRY: "EE",
    Token.EXIT: "XX",
}

_BLOCK = "██"

# Where the wall of a cell lands on the canvas, relative to its top-left
# corner ``(2 * y, 2 * x)``.
_WALL_SPOTS: Dict[int, Tuple[int, int]] = {
    NORTH: (0, 1),
    SOUTH: (2, 1),
    WEST: (1, 0),
    EAST: (1, 2),
}


class Canvas:
    """A ``(2h+1)`` by ``(2w+1)`` grid of :class:`Token` values."""

    def __init__(self, generator: MazeGenerator) -> None:
        """Build the canvas of walls and corridors of ``generator``.

        Args:
            generator: A generator on which ``generate()`` has been
                called.
        """
        self.generator = generator
        self.rows = 2 * generator.height + 1
        self.cols = 2 * generator.width + 1
        self.cells: List[List[Token]] = [
            [Token.VOID] * self.cols for _ in range(self.rows)
        ]
        self._draw_walls()

    def _draw_walls(self) -> None:
        """Fill the canvas with the walls of every cell."""
        generator = self.generator
        for y in range(generator.height):
            for x in range(generator.width):
                self._draw_cell_walls(x, y, generator.walls_at(x, y))
        for row in range(0, self.rows, 2):
            for col in range(0, self.cols, 2):
                if self._post_is_wall(row, col):
                    self.cells[row][col] = Token.WALL

    def _draw_cell_walls(self, x: int, y: int, walls: int) -> None:
        """Draw the closed walls of the cell ``(x, y)``."""
        for direction, (row, col) in _WALL_SPOTS.items():
            if walls & direction:
                self.cells[2 * y + row][2 * x + col] = Token.WALL

    def _post_is_wall(self, row: int, col: int) -> bool:
        """Tell whether the corner at ``(row, col)`` touches a wall."""
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            near_row, near_col = row + delta_row, col + delta_col
            if not (0 <= near_row < self.rows and 0 <= near_col < self.cols):
                continue
            if self.cells[near_row][near_col] is Token.WALL:
                return True
        return False

    def paint_pattern(self) -> None:
        """Give the "42" cells and their walls their own token."""
        pattern = self.generator.pattern_cells
        if not pattern:
            return
        for row in range(self.rows):
            for col in range(self.cols):
                touched = self._cells_touching(row, col)
                if touched and touched & pattern:
                    self.cells[row][col] = Token.PATTERN

    def _cells_touching(self, row: int, col: int) -> Set[Coord]:
        """Return the maze cells sharing the canvas spot ``(row, col)``."""
        xs = [(col - 1) // 2] if col % 2 else [col // 2 - 1, col // 2]
        ys = [(row - 1) // 2] if row % 2 else [row // 2 - 1, row // 2]
        return {
            (x, y)
            for x in xs
            for y in ys
            if 0 <= x < self.generator.width
            and 0 <= y < self.generator.height
        }

    def paint_path(self, path: List[Coord]) -> None:
        """Draw ``path`` as a continuous line of corridors."""
        for x, y in path:
            self.cells[2 * y + 1][2 * x + 1] = Token.PATH
        for (from_x, from_y), (to_x, to_y) in zip(path, path[1:]):
            row = 2 * from_y + 1 + (to_y - from_y)
            col = 2 * from_x + 1 + (to_x - from_x)
            self.cells[row][col] = Token.PATH

    def paint_endpoints(self) -> None:
        """Mark the entry and the exit cells."""
        entry_x, entry_y = self.generator.entry
        exit_x, exit_y = self.generator.exit
        self.cells[2 * entry_y + 1][2 * entry_x + 1] = Token.ENTRY
        self.cells[2 * exit_y + 1][2 * exit_x + 1] = Token.EXIT


def _colour_of(token: Token, theme: Theme, pattern_colour: bool) -> int:
    """Return the ANSI colour index used to draw ``token``."""
    if token is Token.PATTERN:
        return theme.pattern if pattern_colour else theme.wall
    if token is Token.PATH:
        return theme.path
    if token is Token.ENTRY:
        return theme.entry
    if token is Token.EXIT:
        return theme.exit
    return theme.wall


def _swatch(
    token: Token,
    theme: Theme,
    colour: bool,
    pattern_colour: bool,
    count: int = 1,
) -> str:
    """Return ``count`` consecutive spots standing for ``token``.

    Args:
        token: What the spots stand for.
        theme: Colours used for the walls, the path and the pattern.
        colour: Use ANSI colours; ASCII characters are used otherwise.
        pattern_colour: Give the "42" pattern its own colour.
        count: How many spots to draw in a row.

    Returns:
        The drawn spots, colour escape sequences included.
    """
    if not colour or token is Token.VOID:
        return _ASCII[token] * count
    code = _colour_of(token, theme, pattern_colour)
    return f"\x1b[38;5;{code}m{_BLOCK * count}{_RESET}"


def _render_row(
    row: List[Token], theme: Theme, colour: bool, pattern_colour: bool
) -> str:
    """Render a single canvas row, grouping identical tokens together."""
    return "".join(
        _swatch(token, theme, colour, pattern_colour, len(list(group)))
        for token, group in groupby(row)
    )


def render(
    generator: MazeGenerator,
    theme: Theme = THEMES[0],
    show_path: bool = False,
    colour: bool = True,
    pattern_colour: bool = True,
) -> str:
    """Render a maze as a block of text.

    Args:
        generator: A generator on which ``generate()`` has been called.
        theme: Colours used for the walls, the path and the pattern.
        show_path: Draw the shortest path from the entry to the exit.
        colour: Use ANSI colours; ASCII characters are used otherwise.
        pattern_colour: Give the "42" pattern its own colour.

    Returns:
        The rendered maze, without a trailing newline.
    """
    canvas = Canvas(generator)
    canvas.paint_pattern()
    if show_path:
        canvas.paint_path(generator.solution)
    canvas.paint_endpoints()
    return "\n".join(
        _render_row(row, theme, colour, pattern_colour)
        for row in canvas.cells
    )


def legend(theme: Theme, colour: bool, pattern_colour: bool) -> str:
    """Return a one line legend matching the current colours."""
    items = (
        (Token.ENTRY, "entry"),
        (Token.EXIT, "exit"),
        (Token.PATTERN, "42"),
        (Token.PATH, "path"),
        (Token.WALL, "wall"),
    )
    return "  ".join(
        f"{_swatch(token, theme, colour, pattern_colour)} {label}"
        for token, label in items
    )
