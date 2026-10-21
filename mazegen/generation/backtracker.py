"""再帰的バックトラッカーで全域木を掘る。

通路にするセル（region）のすべてを、ループのない 1 本の木でつなぐ。
こうしてできるのが完全迷路で、どの 2 セルの間にも経路がちょうど 1 本
だけある。

木にはループがないので、3x3（2x2 でも）の壁のない区画はできない。
3x3 の規則を確かめる必要があるのは、壁を追加で開ける編み込み
（braiding.py）だけ。
"""

from __future__ import annotations

import random
from typing import List, Set, Tuple

from ..constants import DIRECTIONS, Coord
from ..grid import Grid


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
        # まだ訪れていない隣の通路と、そこへ向かう向きの組。
        unvisited: List[Tuple[int, Coord]] = []
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
