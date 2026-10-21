""""42" のパターンを描くためのビットマップ字形。"""

from __future__ import annotations

from typing import Dict, Set, Tuple

from .constants import Coord

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


def text_width(text: str) -> int:
    """text を等倍で描いたときの横幅（セル数）を返す。"""
    return len(text) * (GLYPH_WIDTH + GLYPH_GAP) - GLYPH_GAP


def text_cells(text: str, scale: int) -> Set[Coord]:
    """text を scale 倍に拡大して描いたときに塗るセルを返す。

    座標は、描いた文字列の左上を (0, 0) とする相対座標。
    """
    cells: Set[Coord] = set()
    for index, char in enumerate(text):
        left = index * (GLYPH_WIDTH + GLYPH_GAP)
        for y, row in enumerate(GLYPHS[char]):
            for x, mark in enumerate(row):
                if mark != "#":
                    continue
                # 等倍の 1 セルを、scale x scale の正方形に広げる。
                for dy in range(scale):
                    for dx in range(scale):
                        cells.add(((left + x) * scale + dx, y * scale + dy))
    return cells
