""""42" のパターンを描くためのビットマップ字形。"""

from __future__ import annotations

from typing import Dict, Set, Tuple

from ..constants import Coord

# 1 文字は横 4 x 縦 7 セル。"#" のセルが、完全に閉じたセルになる。
# 字形の中の穴は必ず 2 セル以上の太さにしてある。1 セル幅の穴は編み込み
# でも開けられない袋小路になり、行き止まりが残ってしまうため。
GLYPHS: Dict[str, Tuple[str, ...]] = {
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

GLYPH_WIDTH = 4
GLYPH_HEIGHT = 7
# 文字と文字の間に空けるセル数。
GLYPH_GAP = 1

PATTERN_TEXT = "42"
# "42" 全体の大きさ（セル数）。
PATTERN_WIDTH = len(PATTERN_TEXT) * (GLYPH_WIDTH + GLYPH_GAP) - GLYPH_GAP
PATTERN_HEIGHT = GLYPH_HEIGHT


def pattern_shape() -> Set[Coord]:
    """"42" を描くセルを返す。座標は "42" の左上を (0, 0) とする相対座標。"""
    cells: Set[Coord] = set()
    for index, char in enumerate(PATTERN_TEXT):
        left = index * (GLYPH_WIDTH + GLYPH_GAP)
        for y, row in enumerate(GLYPHS[char]):
            for x, mark in enumerate(row):
                if mark == "#":
                    cells.add((left + x, y))
    return cells
