""""42" のパターンをどこに置くか。"""

from __future__ import annotations

from typing import Dict, Iterator, List, Optional, Set, Tuple
from .base import MazeBase
from .constants import Coord
from .glyphs import _GLYPH_H, _glyph_shape, _glyph_span

# The pattern is never allowed to eat more than this share of the grid,
# otherwise the maze itself becomes too cramped to stay interesting.
_MAX_PATTERN_RATIO = 0.30

# 中央に置けなかったときに、ずらして試す回数。
_FIT_ATTEMPTS = 25


class PatternMixin(MazeBase):
    """パターンを収める場所を探し、そのセルを予約する。"""

    def _landmarks(self) -> Dict[str, Coord]:
        """パターンで塞いではいけない、四隅と中央を返す。"""
        return {
            "north-west corner": (0, 0),
            "north-east corner": (self.width - 1, 0),
            "south-west corner": (0, self.height - 1),
            "south-east corner": (self.width - 1, self.height - 1),
            "centre": (self.width // 2, self.height // 2),
        }

    def _place_pattern(self) -> Tuple[Set[Coord], Optional[str]]:
        """パターンが収まる位置を探す。収まらなければ空集合と理由を返す。"""
        if not self.pattern or not self.pattern_text:
            return set(), None

        reserved = {self.entry, self.exit, *self._landmarks().values()}
        budget = _MAX_PATTERN_RATIO * self.width * self.height
        span = _glyph_span(self.pattern_text)
        max_scale = min(
            (self.width - 2) // span,
            (self.height - 2) // _GLYPH_H,
        )
        for scale in range(max_scale, 0, -1):
            shape, shape_w, shape_h = _glyph_shape(self.pattern_text, scale)
            if len(shape) > budget:
                continue
            cells = self._fit_shape(shape, shape_w, shape_h, reserved)
            if cells is not None:
                return cells, None

        return set(), (
            f"the {self.pattern_text!r} pattern was skipped: a "
            f"{self.width}x{self.height} maze is too small for it "
            f"(at least {span + 2}x{_GLYPH_H + 2} cells are needed)"
        )

    def _fit_shape(
        self,
        shape: Set[Coord],
        shape_w: int,
        shape_h: int,
        reserved: Set[Coord],
    ) -> Optional[Set[Coord]]:
        """shape を、外周から 1 マス空けて予約セルを避けつつ置ける場所を探す。

        置いた後も残りのセルがすべてつながっている必要がある。置き場所
        が見つからなければ None を返す。
        """
        if shape_w + 2 > self.width or shape_h + 2 > self.height:
            return None
        max_x = self.width - shape_w - 1
        max_y = self.height - shape_h - 1
        # まず中央を試し、駄目なら適当な場所をいくつか当たってみる。
        centred: Coord = (
            min(max(1, (self.width - shape_w) // 2), max_x),
            min(max(1, (self.height - shape_h) // 2), max_y),
        )
        offsets: List[Coord] = [centred] + [
            (self._rng.randint(1, max_x), self._rng.randint(1, max_y))
            for _ in range(_FIT_ATTEMPTS)
        ]
        for off_x, off_y in offsets:
            cells = {(x + off_x, y + off_y) for x, y in shape}
            if cells & reserved:
                continue
            if self._leaves_connected_region(cells):
                return cells
        return None

    def _leaves_connected_region(self, blocked: Set[Coord]) -> bool:
        """blocked 以外のセルが連結のままかを返す。壁はまだ見ない。"""
        free = [cell for cell in self._all_cells() if cell not in blocked]
        if not free:
            return False

        def neighbours(cell: Coord) -> Iterator[Coord]:
            return (
                other
                for _, other in self._steps_from(cell)
                if self._in_bounds(*other) and other not in blocked
            )

        return len(self._flood(free[0], neighbours)) == len(free)
