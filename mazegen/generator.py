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
from .validation import check_arguments, check_seed, check_types


class MazeGenerator:
    """長方形の迷路を作り、解く。

    使い方は MazeGenerator(...) で条件を決めて generate() を呼ぶだけ。
    結果は grid, solution, directions, pattern_cells, pattern_warning,
    seed_used の属性で読める。
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

        perfect を省略すると、subject の PERFECT と同じく False（Pac-Man 盤）。

        Raises:
            MazeError: 引数の型が違う、大きさが範囲外、入口や出口が迷路の外に
                ある、入口と出口が同じセル、または 2x2 で perfect=False の場合。
        """
        check_types(width, height, entry, exit, perfect, seed)
        exit = (width - 1, height - 1) if exit is None else exit
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
        self.directions: str = ""
        self.seed_used: int = 0
        # 「42」以外のセル。通路として掘る対象で、左上から行ごとに並ぶ。
        self._region: List[Coord] = []

    def generate(self, seed: Optional[int] = None) -> MazeGenerator:
        """迷路を最初から作り直し、self を返す。

        Args:
            seed: 今回だけ使うシード。省略するとコンストラクタのシードを
                使い、それも None ならランダムに選ぶ（seed_used に残る）。

        Raises:
            MazeError: seed が整数でない場合と、入口から出口への経路が
                できなかった場合（「42」は残りのセルがつながる位置にしか
                置かないので、こちらは構造上は起きない）。
        """
        check_seed(seed)
        if seed is None:
            seed = self.seed if self.seed is not None else random_seed()
        self.seed_used = seed
        rng = random.Random(seed)

        # 1. 「42」の配置。壁がすべて閉じた格子を作り直し、「42」を置くセルを決める。
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

        # 2. 全域木の生成。「42」以外のセルを、再帰的バックトラッカーで全域木に
        #    掘る。これで完全迷路（ループのない迷路）になる。
        carve_backtracker(self._grid, self._region, rng)

        # 3. 編み込み（Pac-Man 盤のときだけ）。行き止まりの壁をもう 1 枚開ける
        #    ことを、開けられなくなるまで繰り返す。それでもループが MIN_LOOPS
        #    個未満なら、add_loops で MIN_LOOPS 個になるまで壁を開ける。
        if not self.perfect:
            braiding.remove_dead_ends(self._grid, self._region, rng)
            braiding.add_loops(self._grid, self._region, rng, MIN_LOOPS)

        # 4. 最短経路の探索。幅優先探索で、入口から出口までの最短経路を求める。
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
        """1 セルを 16 進数 1 桁（大文字）で表した、迷路の行のリストを返す。"""
        return ["".join(f"{walls:X}" for walls in row) for row in self.grid]
