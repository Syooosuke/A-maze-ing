""""42" のパターンを描くためのビットマップ字形。

状態を持たない純粋な関数だけなので、ここだけは宣言なしで切り離せる。
"""

from __future__ import annotations

from typing import Dict, Iterator, Set, Tuple

from .constants import Coord


# Bitmap font used to draw the mandatory "42" pattern.  Every hole of a
# glyph is at least two cells thick: a one cell wide hole would be a pocket
# the braiding cannot open, and would leave a dead-end behind.
_GLYPHS: Dict[str, Tuple[str, ...]] = {
    "4": (
        "#  #",
        "#  #",
        "#  #",
        "####",
        "   #",
        "   #",
        "   #",
    ),
    "2": (
        "####",
        "   #",
        "   #",
        "####",
        "#   ",
        "#   ",
        "####",
    ),
}

_GLYPH_W = 4

_GLYPH_H = 7

_GLYPH_GAP = 1


def _glyph_span(text: str) -> int:
    """text を等倍で描いたときの横幅をセル数で返す。"""
    return len(text) * (_GLYPH_W + _GLYPH_GAP) - _GLYPH_GAP


def _glyph_pixels(text: str) -> Iterator[Coord]:
    """text を等倍で描いたときに塗るピクセルを順に返す。"""
    for index, char in enumerate(text):
        offset = index * (_GLYPH_W + _GLYPH_GAP)
        for row_index, row in enumerate(_GLYPHS[char]):
            for col_index, mark in enumerate(row):
                if mark == "#":
                    yield offset + col_index, row_index


def _glyph_shape(text: str, scale: int) -> Tuple[Set[Coord], int, int]:
    """text を scale 倍で描いたピクセル座標の集合と、その全体サイズを返す。"""
    cells = {
        (x * scale + dx, y * scale + dy)
        for x, y in _glyph_pixels(text)
        for dy in range(scale)
        for dx in range(scale)
    }
    return cells, _glyph_span(text) * scale, _GLYPH_H * scale
