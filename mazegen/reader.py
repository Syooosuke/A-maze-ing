"""できあがった迷路を読むためのメソッド。MazeGenerator が受け継ぐ。"""

from __future__ import annotations

from typing import Iterator, List, Optional

from . import analysis
from .constants import Coord
from .grid import Grid


class MazeReader:
    """迷路の壁、経路、統計を読むメソッドの集まり。座標は (x, y)。

    状態は持たず、MazeGenerator が用意する属性を読むだけ。
    """

    entry: Coord
    exit: Coord
    grid: List[List[int]]
    _grid: Grid
    _region: List[Coord]

    def solve(
        self, start: Optional[Coord] = None, goal: Optional[Coord] = None
    ) -> List[Coord]:
        """start から goal までの最短経路を返す。省略時は入口から出口。"""
        return analysis.solve(
            self._grid,
            self.entry if start is None else start,
            self.exit if goal is None else goal,
        )

    @staticmethod
    def path_to_directions(path: List[Coord]) -> str:
        """セルの並びを "ESSW..." のような向きの文字列に変える。"""
        return analysis.path_to_directions(path)

    def walls_at(self, x: int, y: int) -> int:
        """セル (x, y) の閉じた壁のビットマスクを返す。"""
        return self._grid.walls[y][x]

    def is_open(self, x: int, y: int, direction: int) -> bool:
        """(x, y) から direction へ壁を通らずに進めるかを返す。"""
        return not self._grid.has_wall((x, y), direction)

    def open_neighbours(self, x: int, y: int) -> Iterator[Coord]:
        """(x, y) から 1 歩で行けるセルを返す。"""
        return self._grid.open_neighbours((x, y))

    def degree(self, x: int, y: int) -> int:
        """(x, y) の開いている壁の枚数を返す。"""
        return self._grid.degree((x, y))

    def is_block_open(self, x: int, y: int, width: int, height: int) -> bool:
        """(x, y) を左上とする区画の内側に、壁が 1 枚もないかを返す。"""
        return self._grid.is_block_open(x, y, width, height)

    def dead_ends(self) -> List[Coord]:
        """行き止まり（開いた壁が 1 枚だけの通路セル）を返す。"""
        return analysis.dead_ends(self._grid, self._region)

    def loop_count(self) -> int:
        """独立したループの数を返す。完全迷路なら 0。"""
        return analysis.loop_count(self._grid, self._region)

    def to_hex_lines(self) -> List[str]:
        """迷路を 1 セル 16 進数 1 桁で表した行のリストを返す。"""
        return ["".join(f"{walls:x}" for walls in row) for row in self.grid]
