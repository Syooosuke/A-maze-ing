"""生成した迷路が要件を満たしているかの自己検証。"""

from __future__ import annotations

from typing import Iterator, List, Tuple
from .analysis import AnalysisMixin
from .constants import ALL_WALLS, Coord, EAST, NORTH, SOUTH, WEST, _OPPOSITE

from .pattern import PatternMixin


class VerifyMixin(AnalysisMixin, PatternMixin):
    """subject の要件に照らして、満たしていない点を挙げる。"""

    def check(self) -> List[str]:
        """生成した迷路が要件を満たしているか検証する。

        Returns:
            見つかった問題点。すべて満たしていれば空のリスト。
        """
        problems: List[str] = []
        problems.extend(self._check_borders())
        problems.extend(self._check_coherence())
        problems.extend(self._check_pattern())
        problems.extend(self._check_areas())
        if self._component_count() != 1:
            problems.append(
                "the corridors are not fully connected: "
                "some cells are isolated"
            )
        elif not self.perfect:
            problems.extend(self._check_playable())
        elif self.loop_count() != 0:
            problems.append("a perfect maze must not contain any loop")
        return problems

    def _border_walls(self) -> Iterator[Tuple[Coord, int, str]]:
        """外周に面するセルと、閉じているべき壁と、その辺の名前を返す。"""
        for x in range(self.width):
            yield (x, 0), NORTH, "north"
            yield (x, self.height - 1), SOUTH, "south"
        for y in range(self.height):
            yield (0, y), WEST, "west"
            yield (self.width - 1, y), EAST, "east"

    def _check_borders(self) -> List[str]:
        """迷路の外周の壁がすべて閉じているかを確かめる。"""
        return [
            f"cell {x},{y} opens through the {name} border"
            for (x, y), wall, name in self._border_walls()
            if not self.grid[y][x] & wall
        ]

    def _check_coherence(self) -> List[str]:
        """隣り合うセルが共有する壁について一致しているか確かめる。"""
        problems: List[str] = []
        for x, y in self._all_cells():
            for direction in (EAST, SOUTH):
                other_x, other_y = self._step(x, y, direction)
                if not self._in_bounds(other_x, other_y):
                    continue
                mine = bool(self.grid[y][x] & direction)
                theirs = bool(
                    self.grid[other_y][other_x] & _OPPOSITE[direction]
                )
                if mine != theirs:
                    problems.append(
                        f"cells {x},{y} and {other_x},{other_y} "
                        "disagree on their shared wall"
                    )
        return problems

    def _check_pattern(self) -> List[str]:
        """パターンのセルが完全に閉じたままかを確かめる。"""
        return [
            f"pattern cell {x},{y} is not fully closed"
            for x, y in sorted(self.pattern_cells)
            if self.grid[y][x] != ALL_WALLS
        ]

    def _check_areas(self) -> List[str]:
        """3x3 の区画が完全に開いていないかを確かめる。"""
        return [
            f"the 3x3 area at {x},{y} is completely open"
            for y in range(self.height - 2)
            for x in range(self.width - 2)
            if self.is_block_open(x, y, 3, 3)
        ]

    def _check_playable(self) -> List[str]:
        """Pac-Man 盤（非完全迷路）に固有の規則を確かめる。"""
        problems: List[str] = []
        if self.loop_count() < 2:
            problems.append(
                "a playable board needs at least two independent routes"
            )
        for name, (x, y) in self._landmarks().items():
            if (x, y) in self.pattern_cells or self.degree(x, y) == 0:
                problems.append(f"the {name} is not an open corridor")
        ends = self.dead_ends()
        if len(ends) > 2:
            listed = ", ".join(f"{x},{y}" for x, y in ends[:5])
            problems.append(
                f"a playable board should not keep {len(ends)} "
                f"dead-ends ({listed}...)"
            )
        return problems
