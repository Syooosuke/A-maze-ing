"""迷路を描くための中間表現。何をどこに描くかだけを決め、色は持たない。

迷路の 1 セルを、キャンバスでは縦横 3 マスで表す（隣のセルと壁のマスを
共有するので、実際には 2 マスずつずれて並ぶ）::

    +--+--+        セル (x, y) の中心は (行, 列) = (2y+1, 2x+1)。
    |  |  |        中心の上下左右のマスがそのセルの壁、
    +--+--+        斜めのマスが壁と壁の継ぎ目（角）になる。

キャンバス全体は (2 * height + 1) 行 x (2 * width + 1) 列になる。
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Tuple

from mazegen import EAST, NORTH, SOUTH, WEST, Coord, MazeGenerator


class Token(Enum):
    """キャンバスの 1 マスに何を描くか。"""

    VOID = "void"
    WALL = "wall"
    PATTERN = "pattern"
    PATH = "path"
    ENTRY = "entry"
    EXIT = "exit"


# セルの中心から見た、各向きの壁のマスの位置 (行のずれ, 列のずれ)。
WALL_OFFSETS: Dict[int, Tuple[int, int]] = {
    NORTH: (-1, 0),
    SOUTH: (1, 0),
    WEST: (0, -1),
    EAST: (0, 1),
}


class Canvas:
    """Token を並べた 2 次元の格子。cells[行][列] で読み書きする。"""

    def __init__(self, generator: MazeGenerator) -> None:
        """generator の迷路の壁を描いたキャンバスを作る。"""
        self.generator = generator
        self.rows = 2 * generator.height + 1
        self.cols = 2 * generator.width + 1
        self.cells: List[List[Token]] = [
            [Token.VOID] * self.cols for _ in range(self.rows)
        ]
        self._draw_walls()
        self._draw_corners()

    def _draw_walls(self) -> None:
        """各セルの閉じた壁を、壁のマスに描く。"""
        for y in range(self.generator.height):
            for x in range(self.generator.width):
                walls = self.generator.grid[y][x]
                for direction, (d_row, d_col) in WALL_OFFSETS.items():
                    if walls & direction:
                        self.cells[2 * y + 1 + d_row][2 * x + 1 + d_col] = (
                            Token.WALL
                        )

    def _draw_corners(self) -> None:
        """壁と壁の継ぎ目（行も列も偶数のマス）を、壁に接していれば埋める。"""
        for row in range(0, self.rows, 2):
            for col in range(0, self.cols, 2):
                around = [
                    (row - 1, col), (row + 1, col),
                    (row, col - 1), (row, col + 1),
                ]
                for near_row, near_col in around:
                    inside = (
                        0 <= near_row < self.rows and 0 <= near_col < self.cols
                    )
                    if inside and self.cells[near_row][near_col] is Token.WALL:
                        self.cells[row][col] = Token.WALL
                        break

    def paint_pattern(self) -> None:
        """"42" のセルを、壁と角のマスも含めた 3x3 ごと PATTERN で塗る。"""
        for x, y in self.generator.pattern_cells:
            for row in range(2 * y, 2 * y + 3):
                for col in range(2 * x, 2 * x + 3):
                    self.cells[row][col] = Token.PATTERN

    def paint_path(self, path: List[Coord]) -> None:
        """path のセルの中心と、その間の壁のマスを PATH にして線でつなぐ。"""
        for x, y in path:
            self.cells[2 * y + 1][2 * x + 1] = Token.PATH
        for (from_x, from_y), (to_x, to_y) in zip(path, path[1:]):
            # 隣り合う 2 つの中心の、ちょうど真ん中のマス。
            self.cells[from_y + to_y + 1][from_x + to_x + 1] = Token.PATH

    def paint_endpoints(self) -> None:
        """入口と出口のセルの中心に印を付ける。"""
        entry_x, entry_y = self.generator.entry
        exit_x, exit_y = self.generator.exit
        self.cells[2 * entry_y + 1][2 * entry_x + 1] = Token.ENTRY
        self.cells[2 * exit_y + 1][2 * exit_x + 1] = Token.EXIT


def draw_maze(generator: MazeGenerator, show_path: bool) -> Canvas:
    """壁、"42"、（必要なら）最短経路、入口と出口を描いたキャンバスを返す。

    後から塗ったものが上に重なる。入口と出口は経路より上に描く。
    """
    canvas = Canvas(generator)
    canvas.paint_pattern()
    if show_path:
        canvas.paint_path(generator.solution)
    canvas.paint_endpoints()
    return canvas
