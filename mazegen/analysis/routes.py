"""できあがった迷路を調べる。最短経路、ループの数、行き止まり。"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List, Sequence, Set

from ..constants import DELTA, LETTER, Coord
from ..errors import MazeError
from ..grid import Grid, corridor_edges


def solve(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    """start から goal までの最短経路を、幅優先探索で求める。

    Returns:
        start から goal までのセルの並び（両端を含む）。
        つながっていなければ空のリスト。
    """
    came_from: Dict[Coord, Coord] = {}
    seen: Set[Coord] = {start}
    queue: Deque[Coord] = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for other in grid.open_neighbours(cell):
            if other not in seen:
                seen.add(other)
                came_from[other] = cell
                queue.append(other)
    if goal not in seen:
        return []

    # goal から came_from を逆にたどり、最後に向きを反転する。
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def path_to_directions(path: Sequence[Coord]) -> str:
    """隣り合うセルの並びを "ESSW..." のような向きの文字列に変える。

    Raises:
        MazeError: 隣り合っていない 2 セルが続いている場合。
    """
    letters: List[str] = []
    for (from_x, from_y), (to_x, to_y) in zip(path, path[1:]):
        step = (to_x - from_x, to_y - from_y)
        matches = [
            LETTER[direction]
            for direction, delta in DELTA.items()
            if delta == step
        ]
        if not matches:
            raise MazeError(
                f"cells {from_x},{from_y} and {to_x},{to_y} are not adjacent"
            )
        letters.append(matches[0])
    return "".join(letters)


def dead_ends(grid: Grid, region: List[Coord]) -> List[Coord]:
    """開いた壁が 1 枚しかない通路セル（行き止まり）を返す。"""
    return [cell for cell in region if grid.degree(cell) == 1]


def count_components(grid: Grid, region: List[Coord]) -> int:
    """通路セルが、壁で隔てられたいくつのかたまりに分かれているかを返す。"""
    seen: Set[Coord] = set()
    components = 0
    for start in region:
        if start in seen:
            continue
        components += 1
        seen.add(start)
        queue: Deque[Coord] = deque([start])
        while queue:
            for other in grid.open_neighbours(queue.popleft()):
                if other not in seen:
                    seen.add(other)
                    queue.append(other)
    return components


def loop_count(grid: Grid, region: List[Coord]) -> int:
    """独立したループの数を返す。

    通路をグラフ（セルが頂点、開いた壁が辺）とみなしたときの
    「辺の数 - 頂点の数 + 連結成分の数」。木（完全迷路）なら 0 になり、
    壁を 1 枚開けるたびに 1 つ増える。
    """
    open_walls = sum(
        1 for cell, direction in corridor_edges(grid, region)
        if not grid.has_wall(cell, direction)
    )
    return open_walls - len(region) + count_components(grid, region)
