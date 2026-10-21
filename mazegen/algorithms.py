"""全域木を掘る 3 つのアルゴリズム。

どれも、通路にするセル（region）のすべてを、ループのない 1 本の木で
つなぐ。こうしてできるのが完全迷路で、どの 2 セルの間にも経路がちょうど
1 本だけある。
"""

from __future__ import annotations

import random
from typing import Dict, List, Set, Tuple

from .constants import DIRECTIONS, Coord
from .grid import Grid, corridor_edges


def carve_backtracker(
    grid: Grid, region: List[Coord], rng: random.Random
) -> None:
    """再帰的バックトラッカー（ランダムな深さ優先探索）で掘る。

    行けるところまで進み、行き止まったら 1 歩ずつ戻って別の道を探す。
    長く曲がりくねった通路ができる。再帰の代わりにスタックを使う。
    """
    corridors = set(region)
    start = rng.choice(region)
    visited: Set[Coord] = {start}
    stack: List[Coord] = [start]
    while stack:
        cell = stack[-1]
        unvisited = []
        for direction in DIRECTIONS:
            other = grid.neighbour(cell, direction)
            if other in corridors and other not in visited:
                unvisited.append((direction, other))
        if not unvisited:
            stack.pop()
            continue
        direction, other = rng.choice(unvisited)
        grid.open_wall(cell, direction)
        visited.add(other)
        stack.append(other)


def carve_prim(grid: Grid, region: List[Coord], rng: random.Random) -> None:
    """ランダム化した Prim 法で掘る。

    掘り終えた部分に面している壁（frontier）の中からランダムに 1 枚を
    選び、その先が未訪問なら開けて広げていく。
    """
    corridors = set(region)
    start = rng.choice(region)
    visited: Set[Coord] = {start}
    frontier: List[Tuple[Coord, int]] = []
    _add_frontier(grid, start, corridors, visited, frontier)
    while frontier:
        cell, direction = frontier.pop(rng.randrange(len(frontier)))
        other = grid.neighbour(cell, direction)
        if other in visited:
            continue
        grid.open_wall(cell, direction)
        visited.add(other)
        _add_frontier(grid, other, corridors, visited, frontier)


def _add_frontier(
    grid: Grid,
    cell: Coord,
    corridors: Set[Coord],
    visited: Set[Coord],
    frontier: List[Tuple[Coord, int]],
) -> None:
    """cell の壁のうち、まだ訪れていない通路に面するものを frontier に足す。"""
    for direction in DIRECTIONS:
        other = grid.neighbour(cell, direction)
        if other in corridors and other not in visited:
            frontier.append((cell, direction))


def carve_kruskal(
    grid: Grid, region: List[Coord], rng: random.Random
) -> None:
    """ランダム化した Kruskal 法で掘る。

    通路どうしの間の壁をすべてランダムな順に並べ、壁の両側がまだ別々の
    かたまりなら開ける。かたまりの管理には Union-Find を使う。
    """
    walls = list(corridor_edges(grid, region))
    rng.shuffle(walls)
    # parent[cell] をたどった先の根が、そのセルが属するかたまりの代表。
    parent: Dict[Coord, Coord] = {cell: cell for cell in region}

    def find_root(cell: Coord) -> Coord:
        root = cell
        while parent[root] != root:
            root = parent[root]
        # 次回からすぐ根に届くよう、通ったセルを根に直接つなぎ直す。
        while parent[cell] != root:
            next_cell = parent[cell]
            parent[cell] = root
            cell = next_cell
        return root

    for cell, direction in walls:
        root_a = find_root(cell)
        root_b = find_root(grid.neighbour(cell, direction))
        if root_a == root_b:
            continue  # 開けるとループになる
        parent[root_a] = root_b
        grid.open_wall(cell, direction)
