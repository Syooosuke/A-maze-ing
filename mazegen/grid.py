"""迷路の格子。セルごとの壁と、それを読み書きする操作。"""

from __future__ import annotations

from typing import Iterator, List, Tuple

from .constants import ALL_WALLS, DELTA, DIRECTIONS, EAST, OPPOSITE, SOUTH
from .constants import Coord


class Grid:
    """width x height 個のセルと、その壁を持つ格子。

    walls[y][x] がセル (x, y) の閉じた壁のビットマスク。壁を開け閉め
    するときは必ず両側のセルを同時に書き換えるので、隣り合うセルの間で
    壁の情報が食い違うことはない。
    """

    def __init__(self, width: int, height: int) -> None:
        """すべての壁が閉じた格子を作る。"""
        self.width = width
        self.height = height
        self.walls: List[List[int]] = [
            [ALL_WALLS] * width for _ in range(height)
        ]

    def in_bounds(self, cell: Coord) -> bool:
        """cell が格子の内側にあるかを返す。"""
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def cells(self) -> Iterator[Coord]:
        """すべてのセルを、左上から 1 行ずつ順に返す。"""
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def neighbour(self, cell: Coord, direction: int) -> Coord:
        """cell から direction へ 1 歩進んだセルを返す。格子の外もありうる。"""
        x, y = cell
        dx, dy = DELTA[direction]
        return x + dx, y + dy

    def has_wall(self, cell: Coord, direction: int) -> bool:
        """cell の direction 側の壁が閉じているかを返す。"""
        x, y = cell
        return bool(self.walls[y][x] & direction)

    def open_wall(self, cell: Coord, direction: int) -> None:
        """cell と、direction 側の隣のセルとの間の壁を開ける。"""
        x, y = cell
        other_x, other_y = self.neighbour(cell, direction)
        self.walls[y][x] &= ~direction
        self.walls[other_y][other_x] &= ~OPPOSITE[direction]

    def close_wall(self, cell: Coord, direction: int) -> None:
        """cell と、direction 側の隣のセルとの間の壁を閉じる。"""
        x, y = cell
        other_x, other_y = self.neighbour(cell, direction)
        self.walls[y][x] |= direction
        self.walls[other_y][other_x] |= OPPOSITE[direction]

    def open_neighbours(self, cell: Coord) -> Iterator[Coord]:
        """cell から壁を通らずに 1 歩で行けるセルを返す。"""
        for direction in DIRECTIONS:
            other = self.neighbour(cell, direction)
            if not self.has_wall(cell, direction) and self.in_bounds(other):
                yield other

    def degree(self, cell: Coord) -> int:
        """cell の 4 枚の壁のうち、開いている枚数を返す。"""
        return sum(
            1 for direction in DIRECTIONS
            if not self.has_wall(cell, direction)
        )

    def is_block_open(self, x: int, y: int, width: int, height: int) -> bool:
        """(x, y) を左上とする width x height の区画に、内側の壁がないかを返す。

        区画の外周の壁は見ない。区画が格子からはみ出すなら False。
        """
        if x + width > self.width or y + height > self.height:
            return False
        for row in range(y, y + height):
            for col in range(x, x + width):
                is_last_col = col == x + width - 1
                is_last_row = row == y + height - 1
                if not is_last_col and self.walls[row][col] & EAST:
                    return False
                if not is_last_row and self.walls[row][col] & SOUTH:
                    return False
        return True


def corridor_edges(
    grid: Grid, region: List[Coord]
) -> Iterator[Tuple[Coord, int]]:
    """通路セルどうしが共有する壁を、1 枚につき 1 回ずつ返す。

    各セルの東と南の壁だけを見る。こうすると、2 つのセルの間の壁を
    左側（または上側）のセルからだけ数えることになり、重複しない。
    壁が開いているかどうかは問わない。

    Returns:
        (セル, EAST または SOUTH) の組。
    """
    corridors = set(region)
    for cell in region:
        for direction in (EAST, SOUTH):
            if grid.neighbour(cell, direction) in corridors:
                yield cell, direction
