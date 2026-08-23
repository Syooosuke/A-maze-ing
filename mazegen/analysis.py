"""できあがった迷路を調べる。経路探索と統計。"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Sequence, Set
from .base import MazeBase
from .constants import Coord, _STEP_LETTER
from .errors import MazeError


class AnalysisMixin(MazeBase):
    """最短経路、連結成分、ループ数、行き止まりを数える。"""

    def dead_ends(self) -> List[Coord]:
        """開いた壁が 1 枚しかない通路セルを返す。"""
        return [cell for cell in self._region if self.degree(*cell) == 1]

    def loop_count(self) -> int:
        """独立したループの数（循環的複雑度）を返す。"""
        edges = sum(1 for _ in self._open_edges())
        return edges - len(self._region) + self._component_count()

    def _reachable_from(self, start: Coord) -> Set[Coord]:
        """開いた壁をたどって start とつながるセルをすべて返す。"""
        return self._flood(start, lambda cell: self.open_neighbours(*cell))

    def _component_count(self) -> int:
        """通路セルの連結成分の数を数える。"""
        seen: Set[Coord] = set()
        components = 0
        for cell in self._region:
            if cell in seen:
                continue
            components += 1
            seen |= self._reachable_from(cell)
        return components

    def solve(
        self,
        start: Optional[Coord] = None,
        goal: Optional[Coord] = None,
    ) -> List[Coord]:
        """start から goal までの最短経路を返す。

        どちらも省略すると入口から出口までを解く。つながっていなければ
        空のリストを返す。
        """
        source = self.entry if start is None else start
        target = self.exit if goal is None else goal
        if not self.grid:
            return []
        previous: Dict[Coord, Coord] = {}
        seen: Set[Coord] = {source}
        queue: deque[Coord] = deque([source])
        while queue:
            current = queue.popleft()
            if current == target:
                break
            for neighbour in self.open_neighbours(*current):
                if neighbour in seen:
                    continue
                seen.add(neighbour)
                previous[neighbour] = current
                queue.append(neighbour)
        if target not in seen:
            return []
        path: List[Coord] = [target]
        while path[-1] != source:
            path.append(previous[path[-1]])
        path.reverse()
        return path

    @staticmethod
    def path_to_directions(path: Sequence[Coord]) -> str:
        """隣接するセルの並びを N/E/S/W の文字列に変換する。"""
        letters: List[str] = []
        for (from_x, from_y), (to_x, to_y) in zip(path, path[1:]):
            letter = _STEP_LETTER.get((to_x - from_x, to_y - from_y))
            if letter is None:
                raise MazeError(
                    f"cells {from_x},{from_y} and {to_x},{to_y} "
                    "are not adjacent"
                )
            letters.append(letter)
        return "".join(letters)
