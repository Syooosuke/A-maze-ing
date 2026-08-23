"""公開クラス MazeGenerator の組み立て。"""

from __future__ import annotations

import random
from typing import List, Optional, Set
from .carving import CarvingMixin
from .constants import (
    ALGORITHMS,
    ALL_WALLS,
    Coord,
    MAX_SIZE,
    MIN_SIZE,
    random_seed,
)
from .errors import MazeError
from .glyphs import _GLYPHS

from .verify import VerifyMixin


class MazeGenerator(CarvingMixin, VerifyMixin):
    """長方形の迷路を作り、編み込み、解く。

    壁はセルごとのビットマスクとして持つので、迷路の実体は
    List[List[int]] にすぎない。壁は必ず両側のセルへ同時に書き込むため、
    構造は作り方の時点で整合している。"""

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
        """引数を検証し、空の迷路を用意する。"""
        if width < MIN_SIZE or height < MIN_SIZE:
            raise MazeError(
                f"maze size must be at least {MIN_SIZE}x{MIN_SIZE} cells"
            )
        if width > MAX_SIZE or height > MAX_SIZE:
            raise MazeError(
                f"maze size must not exceed {MAX_SIZE}x{MAX_SIZE} cells"
            )
        if algorithm not in ALGORITHMS:
            known = ", ".join(ALGORITHMS)
            raise MazeError(
                f"unknown algorithm {algorithm!r} (known: {known})"
            )
        for char in pattern_text:
            if char not in _GLYPHS:
                raise MazeError(f"no glyph available for {char!r}")

        self.width = width
        self.height = height
        self.entry = entry
        self.exit = (width - 1, height - 1) if exit is None else exit
        self.perfect = perfect
        self.seed = seed
        self.algorithm = algorithm
        self.pattern = pattern
        self.pattern_text = pattern_text

        self._check_endpoint(self.entry, "ENTRY")
        self._check_endpoint(self.exit, "EXIT")
        if self.entry == self.exit:
            raise MazeError("entry and exit must be different cells")

        self.grid: List[List[int]] = []
        self.pattern_cells: Set[Coord] = set()
        self.pattern_warning: Optional[str] = None
        self.solution: List[Coord] = []
        self.directions = ""
        self.seed_used = 0
        self._region: List[Coord] = []
        self._rng = random.Random(seed)

    def generate(self, seed: Optional[int] = None) -> "MazeGenerator":
        """迷路をまるごと作り直し、self を返す。

        seed を渡すとコンストラクタに渡したシードを上書きする。どちらも
        None のときはランダムなシードを引き、seed_used に記録する。
        """
        base = seed if seed is not None else self.seed
        if base is None:
            base = random_seed()
        self.seed_used = base
        self._rng = random.Random(base)

        self.grid = [[ALL_WALLS] * self.width for _ in range(self.height)]
        self.pattern_cells, self.pattern_warning = self._place_pattern()
        self._region = [
            cell for cell in self._all_cells()
            if cell not in self.pattern_cells
        ]
        if not self._region:
            raise MazeError("the pattern leaves no room for the maze")

        self._carve_spanning_tree()
        if not self.perfect:
            self._braid()
            self._add_loops(2)

        self.solution = self.solve()
        if not self.solution:
            raise MazeError("no path between the entry and the exit")
        self.directions = self.path_to_directions(self.solution)
        return self

    def _check_endpoint(self, cell: Coord, label: str) -> None:
        """cell が格子の外なら MazeError を送出する。"""
        x, y = cell
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise MazeError(
                f"{label} {x},{y} is outside the "
                f"{self.width}x{self.height} maze"
            )
