"""公開クラス MazeGenerator。生成の手順を上から順に呼び出す。"""

from __future__ import annotations

import random
from typing import List, Optional, Set

from .analysis import routes
from .analysis.verify import find_problems
from .constants import Coord, random_seed
from .errors import MazeError
from .grid import Grid
from .generation import algorithms, braiding
from .generation.pattern import landmarks, place_pattern
from .reader import MazeReader
from .validation import check_arguments

# ALGORITHM の名前から、全域木を掘る関数を引く表。
CARVERS = {
    "backtracker": algorithms.carve_backtracker,
    "prim": algorithms.carve_prim,
    "kruskal": algorithms.carve_kruskal,
}


class MazeGenerator(MazeReader):
    """長方形の迷路を作り、解く。

    使い方は MazeGenerator(...) で条件を決めて generate() を呼ぶだけ。
    結果は grid, solution, directions, pattern_cells などの属性と、
    MazeReader から受け継いだ walls_at() などのメソッドで読める。
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Coord = (0, 0),
        exit: Optional[Coord] = None,
        perfect: bool = True,
        seed: Optional[int] = None,
        algorithm: str = "backtracker",
        pattern: bool = True,
        pattern_text: str = "42",
    ) -> None:
        """条件を検証して保存する。迷路はまだ作らない。

        Raises:
            MazeError: 条件では迷路を作れない場合。
        """
        if exit is None:
            exit = (width - 1, height - 1)
        check_arguments(width, height, entry, exit, algorithm, pattern_text)
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.seed = seed
        self.algorithm = algorithm
        self.pattern = pattern
        self.pattern_text = pattern_text

        # generate() の結果。それまでは壁がすべて閉じた格子になっている。
        self._grid = Grid(width, height)
        self.grid: List[List[int]] = self._grid.walls
        self.pattern_cells: Set[Coord] = set()
        self.pattern_warning: Optional[str] = None
        self.solution: List[Coord] = []
        self.directions = ""
        self.seed_used = 0
        # パターン以外のセル。通路として掘る対象で、左上から行ごとに並ぶ。
        self._region: List[Coord] = []

    def generate(self, seed: Optional[int] = None) -> MazeGenerator:
        """迷路を最初から作り直し、self を返す。

        Args:
            seed: 今回だけ使うシード。省略するとコンストラクタのシードを
                使い、それも None ならランダムに選ぶ（seed_used に残る）。
        """
        if seed is None:
            seed = self.seed if self.seed is not None else random_seed()
        self.seed_used = seed
        rng = random.Random(seed)

        # 1. 壁がすべて閉じた格子に、"42" のパターンの場所を決める。
        self._grid = Grid(self.width, self.height)
        self.grid = self._grid.walls
        self.pattern_cells, self.pattern_warning = set(), None
        if self.pattern and self.pattern_text:
            reserved = {self.entry, self.exit}
            reserved.update(landmarks(self.width, self.height).values())
            self.pattern_cells, self.pattern_warning = place_pattern(
                self.width, self.height, self.pattern_text, reserved, rng
            )
        self._region = [
            cell for cell in self._grid.cells()
            if cell not in self.pattern_cells
        ]

        # 2. 残りのセルを全域木で掘る。これで完全迷路になる。
        CARVERS[self.algorithm](self._grid, self._region, rng)

        # 3. Pac-Man 盤なら、行き止まりをなくしてループを 2 つ以上にする。
        if not self.perfect:
            braiding.remove_dead_ends(self._grid, self._region, rng)
            braiding.add_loops(self._grid, self._region, rng, target=2)

        # 4. 入口から出口までの最短経路を求める。
        self.solution = self.solve()
        if not self.solution:
            raise MazeError("no path between the entry and the exit")
        self.directions = routes.path_to_directions(self.solution)
        return self

    def check(self) -> List[str]:
        """要件を満たしていない点を返す。問題がなければ空のリスト。"""
        return find_problems(
            self._grid, self._region, self.pattern_cells, self.perfect
        )
