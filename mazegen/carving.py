"""通路を掘る。全域木アルゴリズムと編み込み。"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple
from .analysis import AnalysisMixin
from .constants import Coord


class CarvingMixin(AnalysisMixin):
    """全域木を掘り、Pac-Man 盤なら行き止まりをつぶす。"""

    def _carve_spanning_tree(self) -> None:
        """パターン以外のすべてのセルに全域木を掘る。"""
        if self.algorithm == "prim":
            self._carve_prim()
        elif self.algorithm == "kruskal":
            self._carve_kruskal()
        else:
            self._carve_backtracker()

    def _carve_backtracker(self) -> None:
        """ランダム化した深さ優先探索（再帰的バックトラッカー）。"""
        start = self._rng.choice(self._region)
        visited: Set[Coord] = {start}
        stack: List[Coord] = [start]
        while stack:
            x, y = stack[-1]
            options = [
                (direction, cell)
                for direction, cell in self._steps_from((x, y))
                if cell not in visited and self._is_corridor(*cell)
            ]
            if not options:
                stack.pop()
                continue
            direction, cell = self._rng.choice(options)
            self._carve(x, y, direction)
            visited.add(cell)
            stack.append(cell)

    def _carve_prim(self) -> None:
        """ランダム化した Prim のアルゴリズム。"""
        start = self._rng.choice(self._region)
        visited: Set[Coord] = {start}
        frontier: List[Tuple[Coord, int]] = []
        self._push_frontier(start, visited, frontier)
        while frontier:
            index = self._rng.randrange(len(frontier))
            (x, y), direction = frontier.pop(index)
            cell = self._step(x, y, direction)
            if cell in visited:
                continue
            self._carve(x, y, direction)
            visited.add(cell)
            self._push_frontier(cell, visited, frontier)

    def _push_frontier(
        self,
        cell: Coord,
        visited: Set[Coord],
        frontier: List[Tuple[Coord, int]],
    ) -> None:
        """cell の壁のうち、未訪問の通路に面するものを記録する。"""
        frontier.extend(
            (cell, direction)
            for direction, neighbour in self._steps_from(cell)
            if self._is_corridor(*neighbour) and neighbour not in visited
        )

    def _carve_kruskal(self) -> None:
        """Union-Find を使う、ランダム化した Kruskal のアルゴリズム。"""
        edges: List[Tuple[Coord, int]] = list(self._corridor_edges())
        self._rng.shuffle(edges)
        parent: Dict[Coord, Coord] = {cell: cell for cell in self._region}

        def find(cell: Coord) -> Coord:
            root = cell
            while parent[root] != root:
                root = parent[root]
            while parent[cell] != root:
                parent[cell], cell = root, parent[cell]
            return root

        for (x, y), direction in edges:
            left = find((x, y))
            right = find(self._step(x, y, direction))
            if left == right:
                continue
            parent[left] = right
            self._carve(x, y, direction)

    def _braid(self) -> None:
        """行き止まりがなくなるまで壁を開ける。

        3x3 の完全な開放区画ができてしまう場合は開けないので、通路の幅
        が 2 セルを超えることはない。
        """
        while True:
            ends = [cell for cell in self._region if self.degree(*cell) <= 1]
            if not ends:
                return
            self._rng.shuffle(ends)
            opened = [self._open_dead_end(x, y) for x, y in ends]
            if not any(opened):
                return

    def _open_dead_end(self, x: int, y: int) -> bool:
        """行き止まり (x, y) から、通りの少ない隣へ壁を 1 枚開ける。

        同じ巡回のうちに隣が先に開かれていることがあるので、まだ
        行き止まりのままかを確かめ直す。開けたなら True を返す。
        """
        if self.degree(x, y) > 1:
            return False
        options = self._openable_walls(x, y)
        if not options:
            return False
        self._rng.shuffle(options)
        options.sort(key=lambda d: self.degree(*self._step(x, y, d)))
        self._carve(x, y, options[0])
        return True

    def _openable_walls(self, x: int, y: int) -> List[int]:
        """(x, y) の壁のうち、安全に開けられるものを列挙する。

        _creates_open_block は壁を試しに開けてみるので最後に置く。
        """
        return [
            direction
            for direction, neighbour in self._steps_from((x, y))
            if self.grid[y][x] & direction
            and self._is_corridor(*neighbour)
            and not self._creates_open_block(x, y, direction)
        ]

    def _add_loops(self, target: int) -> None:
        """迷路のループが target 個になるまで壁を開けていく。"""
        loops = self.loop_count()
        if loops >= target:
            return
        candidates = list(self._closed_edges())
        self._rng.shuffle(candidates)
        for (x, y), direction in candidates:
            if loops >= target:
                return
            if not self.grid[y][x] & direction:
                continue
            if self._creates_open_block(x, y, direction):
                continue
            self._carve(x, y, direction)
            loops += 1
