"""格子そのものの操作。壁の開け閉めと、隣・辺のたどり方。"""

from __future__ import annotations

import random
from abc import ABC
from collections import deque
from typing import Callable, Iterable, Iterator, List, Optional, Set, Tuple

from .constants import EAST, SOUTH, Coord, _DELTA, _DIRECTIONS, _OPPOSITE


class MazeBase(ABC):
    """共有する状態と、格子を直接いじる下位レベルの操作。"""

    # MazeGenerator.__init__ が用意する状態。すべての層がここを見る。
    width: int
    height: int
    entry: Coord
    exit: Coord
    perfect: bool
    seed: Optional[int]
    algorithm: str
    pattern: bool
    pattern_text: str
    grid: List[List[int]]
    pattern_cells: Set[Coord]
    pattern_warning: Optional[str]
    solution: List[Coord]
    directions: str
    seed_used: int
    _region: List[Coord]
    _rng: random.Random

    def _in_bounds(self, x: int, y: int) -> bool:
        """(x, y) が格子に含まれるかどうかを返す。"""
        return 0 <= x < self.width and 0 <= y < self.height

    def _all_cells(self) -> Iterator[Coord]:
        """格子のすべてのセルを、左上から行ごとに返す。"""
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def _is_corridor(self, x: int, y: int) -> bool:
        """(x, y) が迷路を掘り進めてよいセルかどうかを返す。"""
        return self._in_bounds(x, y) and (x, y) not in self.pattern_cells

    def _flood(
        self,
        start: Coord,
        neighbours: Callable[[Coord], Iterable[Coord]],
    ) -> Set[Coord]:
        """start から neighbours をたどって届くセルをすべて返す。"""
        seen: Set[Coord] = {start}
        queue: deque[Coord] = deque([start])
        while queue:
            for cell in neighbours(queue.popleft()):
                if cell not in seen:
                    seen.add(cell)
                    queue.append(cell)
        return seen

    @staticmethod
    def _step(x: int, y: int, direction: int) -> Coord:
        """(x, y) の direction 側の隣のセルを返す。"""
        delta_x, delta_y = _DELTA[direction]
        return x + delta_x, y + delta_y

    def _steps_from(self, cell: Coord) -> Iterator[Tuple[int, Coord]]:
        """cell の四方の、向きと隣のセルの組を返す。隣は格子の外も含む。"""
        x, y = cell
        for direction in _DIRECTIONS:
            yield direction, self._step(x, y, direction)

    def _carve(self, x: int, y: int, direction: int) -> None:
        """(x, y) と隣のセルの間の壁を開ける。"""
        other_x, other_y = self._step(x, y, direction)
        self.grid[y][x] &= ~direction
        self.grid[other_y][other_x] &= ~_OPPOSITE[direction]

    def _close(self, x: int, y: int, direction: int) -> None:
        """(x, y) と隣のセルの間の壁を閉じる。"""
        other_x, other_y = self._step(x, y, direction)
        self.grid[y][x] |= direction
        self.grid[other_y][other_x] |= _OPPOSITE[direction]

    def _creates_open_block(self, x: int, y: int, direction: int) -> bool:
        """壁を開けると 3x3 の開放区画ができるかどうかを返す。"""
        other_x, other_y = self._step(x, y, direction)
        self._carve(x, y, direction)
        found = self._open_block_around(x, y, other_x, other_y)
        self._close(x, y, direction)
        return found

    def _open_block_around(
        self, x: int, y: int, other_x: int, other_y: int
    ) -> bool:
        """与えられた 2 つのセルを含む 3x3 の開放区画を探す。"""
        # 両方のセルを覆える 3x3 区画の左上は、この範囲にしかない。
        first_x = max(0, max(x, other_x) - 2)
        last_x = min(min(x, other_x), self.width - 3)
        first_y = max(0, max(y, other_y) - 2)
        last_y = min(min(y, other_y), self.height - 3)
        for block_y in range(first_y, last_y + 1):
            for block_x in range(first_x, last_x + 1):
                if self.is_block_open(block_x, block_y, 3, 3):
                    return True
        return False

    def is_block_open(self, x: int, y: int, width: int, height: int) -> bool:
        """(x, y) を左上とする区画の内側に、壁が 1 枚も残っていないかを返す。"""
        if x + width > self.width or y + height > self.height:
            return False
        for row in range(y, y + height):
            for col in range(x, x + width):
                walls = self.grid[row][col]
                if col + 1 < x + width and walls & EAST:
                    return False
                if row + 1 < y + height and walls & SOUTH:
                    return False
        return True

    def walls_at(self, x: int, y: int) -> int:
        """セル (x, y) の閉じた壁のビットマスクを返す。"""
        return self.grid[y][x]

    def is_open(self, x: int, y: int, direction: int) -> bool:
        """(x, y) の direction 側の壁が開いているかを返す。"""
        return not self.grid[y][x] & direction

    def open_neighbours(self, x: int, y: int) -> Iterator[Coord]:
        """(x, y) から 1 歩で行けるセルを順に返す。"""
        walls = self.grid[y][x]
        for direction, neighbour in self._steps_from((x, y)):
            if not walls & direction and self._in_bounds(*neighbour):
                yield neighbour

    def degree(self, x: int, y: int) -> int:
        """(x, y) の壁のうち、開いているものの数を返す。"""
        walls = self.grid[y][x]
        return sum(1 for direction in _DIRECTIONS if not walls & direction)

    def to_hex_lines(self) -> List[str]:
        """迷路を 1 セル 16 進数 1 桁の形で、行ごとに返す。"""
        return ["".join(f"{cell:x}" for cell in row) for row in self.grid]

    def _corridor_edges(self) -> Iterator[Tuple[Coord, int]]:
        """通路セルが共有する壁を、1 枚につき 1 回ずつ返す。

        東と南の壁だけを見ることで、2 つのセルの間の壁を北側/西側の
        セルからのみ報告し、重複を避けている。
        """
        for x, y in self._region:
            for direction in (EAST, SOUTH):
                if self._is_corridor(*self._step(x, y, direction)):
                    yield (x, y), direction

    def _closed_edges(self) -> Iterator[Tuple[Coord, int]]:
        """通路セルどうしを隔てている、まだ閉じた壁を返す。"""
        for (x, y), direction in self._corridor_edges():
            if self.grid[y][x] & direction:
                yield (x, y), direction

    def _open_edges(self) -> Iterator[Tuple[Coord, int]]:
        """通路セルどうしをつないでいる、開いた壁を返す。"""
        for (x, y), direction in self._corridor_edges():
            if not self.grid[y][x] & direction:
                yield (x, y), direction
