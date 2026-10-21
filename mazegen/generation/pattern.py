""""42" のパターンを、迷路のどこに置くかを決める。"""

from __future__ import annotations

import random
from collections import deque
from typing import Deque, Dict, List, Optional, Set, Tuple

from ..constants import DELTA, Coord
from .glyphs import GLYPH_HEIGHT, text_cells, text_width

# パターンが格子のこれ以上の割合を占めるなら、もう一段小さく描く。
# 大きすぎると、迷路として遊べる部分が窮屈になる。
MAX_PATTERN_RATIO = 0.30

# 中央に置けなかったときに試す、ランダムな位置の数。
RANDOM_ATTEMPTS = 25


def landmarks(width: int, height: int) -> Dict[str, Coord]:
    """Pac-Man 盤で必ず通路にしておく、四隅と中央のセルを返す。"""
    return {
        "north-west corner": (0, 0),
        "north-east corner": (width - 1, 0),
        "south-west corner": (0, height - 1),
        "south-east corner": (width - 1, height - 1),
        "centre": (width // 2, height // 2),
    }


def place_pattern(
    width: int, height: int, text: str, reserved: Set[Coord],
    rng: random.Random,
) -> Tuple[Set[Coord], Optional[str]]:
    """text のパターンを置くセルを決める。大きい倍率から順に試す。

    reserved（入口、出口、四隅、中央）はパターンで塞がない。

    Returns:
        (パターンのセル, None)。置けなかったときは (空集合, 理由)。
    """
    # 外周に 1 セルずつ余白を残して収まる、いちばん大きな倍率。
    largest_scale = min(
        (width - 2) // text_width(text),
        (height - 2) // GLYPH_HEIGHT,
    )
    for scale in range(largest_scale, 0, -1):
        shape = text_cells(text, scale)
        if len(shape) > MAX_PATTERN_RATIO * width * height:
            continue
        shape_width = text_width(text) * scale
        shape_height = GLYPH_HEIGHT * scale
        cells = _find_position(
            width, height, shape, shape_width, shape_height, reserved, rng
        )
        if cells is not None:
            return cells, None

    needed_width = text_width(text) + 2
    needed_height = GLYPH_HEIGHT + 2
    return set(), (
        f"the {text!r} pattern was skipped: a {width}x{height} maze is "
        f"too small for it (at least {needed_width}x{needed_height} cells "
        f"are needed)"
    )


def _find_position(
    width: int, height: int, shape: Set[Coord], shape_width: int,
    shape_height: int, reserved: Set[Coord], rng: random.Random,
) -> Optional[Set[Coord]]:
    """shape を置ける位置を探し、置いたときのセルを返す。

    外周から 1 セル空けて置き、reserved のセルは塞がない。置いた後も
    残りのセルがすべてつながっている必要がある。まず中央を試し、だめ
    ならランダムな位置をいくつか試す。見つからなければ None。
    """
    max_left = width - shape_width - 1
    max_top = height - shape_height - 1
    centre = (
        min(max(1, (width - shape_width) // 2), max_left),
        min(max(1, (height - shape_height) // 2), max_top),
    )
    # 乱数は先にまとめて引いておく。どこで見つかっても、乱数の消費量が
    # 同じになり、後に続く迷路の生成が安定する。
    randoms = [
        (rng.randint(1, max_left), rng.randint(1, max_top))
        for _ in range(RANDOM_ATTEMPTS)
    ]
    for left, top in [centre] + randoms:
        cells = {(x + left, y + top) for x, y in shape}
        if cells & reserved:
            continue
        if _rest_is_connected(width, height, cells):
            return cells
    return None


def _rest_is_connected(width: int, height: int, blocked: Set[Coord]) -> bool:
    """blocked 以外のセルが上下左右でひとつながりかを返す。壁は見ない。"""
    free: List[Coord] = [
        (x, y) for y in range(height) for x in range(width)
        if (x, y) not in blocked
    ]
    if not free:
        return False
    seen: Set[Coord] = {free[0]}
    queue: Deque[Coord] = deque([free[0]])
    while queue:
        x, y = queue.popleft()
        for dx, dy in DELTA.values():
            other = (x + dx, y + dy)
            inside = 0 <= other[0] < width and 0 <= other[1] < height
            if inside and other not in blocked and other not in seen:
                seen.add(other)
                queue.append(other)
    return len(seen) == len(free)
