"""公開クラス MazeGenerator。生成の手順を上から順に呼び出す。"""

from __future__ import annotations

import random
from typing import List, Optional, Set

from .analysis import routes
from .analysis.verify import find_problems
from .constants import MIN_LOOPS, Coord, random_seed
from .errors import MazeError
from .grid import Grid
from .generation import braiding
from .generation.backtracker import carve_backtracker
from .generation.pattern import landmarks, place_pattern
from .validation import check_arguments


class MazeGenerator:
    """長方形の迷路を作り、解く。

    使い方は MazeGenerator(...) で条件を決めて generate() を呼ぶだけ。
    結果は grid, solution, directions, pattern_cells などの属性で読める。
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Coord = (0, 0),
        exit: Optional[Coord] = None,
        perfect: bool = False,
        seed: Optional[int] = None,
    ) -> None:
        """条件を検証して保存する。迷路はまだ作らない。

        perfect の既定値は subject と同じく False（Pac-Man 盤）。

        Raises:
            MazeError: 条件では迷路を作れない場合。
        """
        if exit is None:
            exit = (width - 1, height - 1)
        check_arguments(width, height, entry, exit, perfect)
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.seed = seed

        # generate() の結果。それまでは壁がすべて閉じた格子になっている。
        # _grid は壁を開け閉めする Grid オブジェクト、grid は利用者に見せる
        # 壁のリストで、_grid.walls と同じリストを指している。
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

        Raises:
            MazeError: 入口から出口への経路ができなかった場合。"42" は残りの
                セルがつながる位置にしか置かないので、通常は起きない。
        """
        if seed is None:
            seed = self.seed if self.seed is not None else random_seed()
        self.seed_used = seed
        rng = random.Random(seed)

        # 1. 壁がすべて閉じた格子に、"42" のパターンの場所を決める。
        self._grid = Grid(self.width, self.height)
        self.grid = self._grid.walls
        reserved = {self.entry, self.exit}
        reserved.update(landmarks(self.width, self.height).values())
        self.pattern_cells, self.pattern_warning = place_pattern(
            self.width, self.height, reserved, rng
        )
        self._region = [
            cell for cell in self._grid.cells()
            if cell not in self.pattern_cells
        ]

        # 2. 残りのセルを、再帰的バックトラッカーで全域木に掘る。
        #    これで完全迷路（ループのない迷路）になる。
        carve_backtracker(self._grid, self._region, rng)

        # 3. Pac-Man 盤なら、行き止まりをなくし、ループを MIN_LOOPS 個以上に
        #    する。行き止まりをなくすだけでたいてい十分なループができる
        #    （config.txt の 25x17・SEED=42 で 41 個）ので、add_loops は何もしないことが多い。
        if not self.perfect:
            braiding.remove_dead_ends(self._grid, self._region, rng)
            braiding.add_loops(self._grid, self._region, rng, MIN_LOOPS)

        # 4. 入口から出口までの最短経路を求める。
        self.solution = routes.solve(self._grid, self.entry, self.exit)
        if not self.solution:
            raise MazeError("no path between the entry and the exit")
        self.directions = routes.path_to_directions(self.solution)
        return self

    def check(self) -> List[str]:
        """要件を満たしていない点を返す。問題がなければ空のリスト。"""
        return find_problems(
            self._grid, self._region, self.pattern_cells, self.perfect
        )

    def dead_ends(self) -> List[Coord]:
        """行き止まり（開いた壁が 1 枚だけの通路セル）を返す。"""
        return routes.dead_ends(self._grid, self._region)

    def loop_count(self) -> int:
        """独立したループの数を返す。完全迷路なら 0。"""
        return routes.loop_count(self._grid, self._region)

    def to_hex_lines(self) -> List[str]:
        """迷路を 1 セル 16 進数 1 桁で表した行のリストを返す。"""
        return ["".join(f"{walls:X}" for walls in row) for row in self.grid]
