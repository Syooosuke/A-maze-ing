""""42" のパターンを、迷路のどこに置くかを決める。"""

from __future__ import annotations

import random
from collections import deque
from typing import Deque, Dict, List, Optional, Set, Tuple

from ..constants import DELTA, Coord
from .glyphs import PATTERN_HEIGHT, PATTERN_WIDTH, pattern_shape

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
    width: int, height: int, reserved: Set[Coord], rng: random.Random
) -> Tuple[Set[Coord], Optional[str]]:
    """"42" のパターンを置くセルを決める。

    外周から 1 セル空けて置き、reserved（入口、出口、四隅、中央）は
    パターンで塞がない。

    Returns:
        (パターンのセル, None)。置けなかったときは (空集合, 理由)。
    """
    reason = (
        f"the '42' pattern was skipped: a {width}x{height} maze is too "
        f"small for it (at least {PATTERN_WIDTH + 2}x{PATTERN_HEIGHT + 2} "
        f"cells are needed)"
    )
    if PATTERN_WIDTH + 2 > width or PATTERN_HEIGHT + 2 > height:
        return set(), reason
    cells = _find_position(
        width, height, pattern_shape(), PATTERN_WIDTH, PATTERN_HEIGHT,
        reserved, rng,
    )
    if cells is None:
        return set(), reason
    return cells, None


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
