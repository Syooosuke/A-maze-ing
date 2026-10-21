"""完全迷路を Pac-Man 盤に変える。行き止まりをなくし、ループを足す。"""

from __future__ import annotations

import random
from typing import List, Set

from ..analysis.routes import loop_count
from ..constants import DIRECTIONS, Coord
from ..grid import Grid, corridor_edges


def remove_dead_ends(
    grid: Grid, region: List[Coord], rng: random.Random
) -> None:
    """行き止まりがなくなるまで、行き止まりの壁を 1 枚ずつ開けていく。

    開けると 3x3 の壁のない区画ができる壁は開けない。そのため、開けられる
    壁が残っていない行き止まりは、そのまま残ることがある。
    """
    corridors = set(region)
    while True:
        ends = [cell for cell in region if grid.degree(cell) <= 1]
        if not ends:
            return
        rng.shuffle(ends)
        opened_any = False
        for cell in ends:
            if _open_dead_end(grid, cell, corridors, rng):
                opened_any = True
        if not opened_any:
            return  # どれも開けられなかった。これ以上は進まない。


def _open_dead_end(
    grid: Grid, cell: Coord, corridors: Set[Coord], rng: random.Random
) -> bool:
    """行き止まり cell の壁を 1 枚開ける。開けたら True を返す。

    同じ巡回の中で、隣のセルが先に壁を開けて、cell がもう行き止まり
    でなくなっていることがある。その場合は何もしない。
    """
    if grid.degree(cell) > 1:
        return False
    candidates = [
        direction
        for direction in DIRECTIONS
        if grid.has_wall(cell, direction)
        and grid.neighbour(cell, direction) in corridors
        and not creates_3x3_area(grid, cell, direction)
    ]
    if not candidates:
        return False
    # 開いた壁の少ない隣を優先する。隣の行き止まりも一緒に解消できる。
    # 同じ数の隣どうしの順番は、先にシャッフルしてランダムにしておく。
    rng.shuffle(candidates)
    candidates.sort(
        key=lambda direction: grid.degree(grid.neighbour(cell, direction))
    )
    grid.open_wall(cell, candidates[0])
    return True


def add_loops(
    grid: Grid, region: List[Coord], rng: random.Random, target: int
) -> None:
    """ループが target 個になるまで、閉じた壁をランダムに開けていく。"""
    loops = loop_count(grid, region)
    if loops >= target:
        return
    closed_walls = [
        (cell, direction)
        for cell, direction in corridor_edges(grid, region)
        if grid.has_wall(cell, direction)
    ]
    rng.shuffle(closed_walls)
    for cell, direction in closed_walls:
        if loops >= target:
            return
        if creates_3x3_area(grid, cell, direction):
            continue
        # 通路は 1 つにつながっているので、壁を 1 枚開けるとループが 1 つ増える。
        grid.open_wall(cell, direction)
        loops += 1


def creates_3x3_area(grid: Grid, cell: Coord, direction: int) -> bool:
    """この壁を開けると、3x3 の壁のない区画ができてしまうかを返す。

    subject は通路の幅を 2 セルまでに制限している。実際に壁を一度開け、
    cell と隣のセルの両方を含む 3x3 区画を調べてから、閉じ直す。
    """
    x, y = cell
    other_x, other_y = grid.neighbour(cell, direction)
    # 2 つのセルを両方とも含む 3x3 区画の、左上の角になりうる範囲。
    first_x = max(0, max(x, other_x) - 2)
    last_x = min(x, other_x, grid.width - 3)
    first_y = max(0, max(y, other_y) - 2)
    last_y = min(y, other_y, grid.height - 3)

    grid.open_wall(cell, direction)
    found = any(
        grid.is_block_open(left, top, 3, 3)
        for top in range(first_y, last_y + 1)
        for left in range(first_x, last_x + 1)
    )
    grid.close_wall(cell, direction)
    return found
