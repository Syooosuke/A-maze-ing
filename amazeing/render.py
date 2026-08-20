"""ANSI カラーを使った迷路の端末描画。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import groupby
from typing import Dict, List, Set, Tuple

from mazegen import EAST, NORTH, SOUTH, WEST, Coord, MazeGenerator

_RESET = "\x1b[0m"


class Token(Enum):
    """描画キャンバスの半セルが何を表すか。"""

    VOID = "void"
    WALL = "wall"
    PATTERN = "pattern"
    PATH = "path"
    ENTRY = "entry"
    EXIT = "exit"


@dataclass(frozen=True)
class Theme:
    """名前を付けた 256 色 ANSI コードの組。

    Attributes:
        name: 対話メニューに表示する、人が読める名前。
        wall: 迷路の壁の色。
        pattern: "42" のパターンの色。
        path: 最短経路の色。
        entry: 入口セルの色。
        exit: 出口セルの色。
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
    """:class:`Token` を並べた ``(2h+1)`` × ``(2w+1)`` の格子。"""

    def __init__(self, generator: MazeGenerator) -> None:
        """``generator`` の壁と通路からキャンバスを組み立てる。

        Args:
            generator: ``generate()`` を呼び終えた生成器。
        """
        self.generator = generator
        self.rows = 2 * generator.height + 1
        self.cols = 2 * generator.width + 1
        self.cells: List[List[Token]] = [
            [Token.VOID] * self.cols for _ in range(self.rows)
        ]
        self._draw_walls()

    def _draw_walls(self) -> None:
        """すべてのセルの壁でキャンバスを埋める。"""
        generator = self.generator
        for y in range(generator.height):
            for x in range(generator.width):
                self._draw_cell_walls(x, y, generator.walls_at(x, y))
        for row in range(0, self.rows, 2):
            for col in range(0, self.cols, 2):
                if self._post_is_wall(row, col):
                    self.cells[row][col] = Token.WALL

    def _draw_cell_walls(self, x: int, y: int, walls: int) -> None:
        """セル ``(x, y)`` の閉じた壁を描く。"""
        for direction, (row, col) in _WALL_SPOTS.items():
            if walls & direction:
                self.cells[2 * y + row][2 * x + col] = Token.WALL

    def _post_is_wall(self, row: int, col: int) -> bool:
        """``(row, col)`` の角が壁に接しているかどうかを返す。"""
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            near_row, near_col = row + delta_row, col + delta_col
            if not (0 <= near_row < self.rows and 0 <= near_col < self.cols):
                continue
            if self.cells[near_row][near_col] is Token.WALL:
                return True
        return False

    def paint_pattern(self) -> None:
        """パターン "42" のセルとその壁に専用トークンを与える。"""
        pattern = self.generator.pattern_cells
        if not pattern:
            return
        for row in range(self.rows):
            for col in range(self.cols):
                touched = self._cells_touching(row, col)
                if touched and touched & pattern:
                    self.cells[row][col] = Token.PATTERN

    def _cells_touching(self, row: int, col: int) -> Set[Coord]:
        """キャンバス上の ``(row, col)`` を共有する迷路セルを返す。"""
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
        """``path`` を途切れない通路の線として描く。"""
        for x, y in path:
            self.cells[2 * y + 1][2 * x + 1] = Token.PATH
        for (from_x, from_y), (to_x, to_y) in zip(path, path[1:]):
            row = 2 * from_y + 1 + (to_y - from_y)
            col = 2 * from_x + 1 + (to_x - from_x)
            self.cells[row][col] = Token.PATH

    def paint_endpoints(self) -> None:
        """入口と出口のセルに印を付ける。"""
        entry_x, entry_y = self.generator.entry
        exit_x, exit_y = self.generator.exit
        self.cells[2 * entry_y + 1][2 * entry_x + 1] = Token.ENTRY
        self.cells[2 * exit_y + 1][2 * exit_x + 1] = Token.EXIT


def _colour_of(token: Token, theme: Theme, pattern_colour: bool) -> int:
    """``token`` を描くのに使う ANSI 色番号を返す。"""
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
    """``token`` を表すマスを ``count`` 個ぶん連ねて返す。

    Args:
        token: マスが表すもの。
        theme: 壁、経路、パターンに使う配色。
        colour: ANSI カラーを使う。偽なら ASCII 文字で描く。
        pattern_colour: "42" のパターンに専用色を与える。
        count: 横に並べて描くマスの個数。

    Returns:
        描いたマス。色のエスケープシーケンスを含む。
    """
    if not colour or token is Token.VOID:
        return _ASCII[token] * count
    code = _colour_of(token, theme, pattern_colour)
    return f"\x1b[38;5;{code}m{_BLOCK * count}{_RESET}"


def _render_row(
    row: List[Token], theme: Theme, colour: bool, pattern_colour: bool
) -> str:
    """キャンバスの 1 行を、同じトークンをまとめながら描画する。"""
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
    """迷路をひとかたまりのテキストとして描画する。

    Args:
        generator: ``generate()`` を呼び終えた生成器。
        theme: 壁、経路、パターンに使う配色。
        show_path: 入口から出口への最短経路を描く。
        colour: ANSI カラーを使う。偽なら ASCII 文字で描く。
        pattern_colour: "42" のパターンに専用色を与える。

    Returns:
        描画した迷路。末尾の改行は含まない。
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
    """いまの配色に対応する凡例を 1 行で返す。"""
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
