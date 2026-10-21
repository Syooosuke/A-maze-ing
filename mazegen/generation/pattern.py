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
    # 外周に 1 セルずつ余白を残すので、"42" の大きさ + 2 が必要。
    needed_width, needed_height = PATTERN_WIDTH + 2, PATTERN_HEIGHT + 2
    if width < needed_width or height < needed_height:
        return set(), (
            f"cannot draw the '42' pattern: a {width}x{height} maze is too "
            f"small for it (at least {needed_width}x{needed_height} cells "
            f"are needed)"
        )
    cells = _find_position(width, height, reserved, rng)
    if cells is None:
        return set(), (
            f"cannot draw the '42' pattern: no place in the {width}x{height} "
            f"maze leaves the entry, the exit, the corners and the centre "
            f"free"
        )
    return cells, None


def _find_position(
    width: int, height: int, reserved: Set[Coord], rng: random.Random
) -> Optional[Set[Coord]]:
    """"42" を置ける位置を探し、置いたときのセルを返す。

    reserved のセルは塞がず、置いた後も残りのセルがすべてつながって
    いる必要がある。まず中央を試し、だめならランダムな位置をいくつか
    試す。見つからなければ None。

    幅が偶数だと、中央のセル（reserved）が "2" の横棒に重なるので、
    中央には置けずランダムな位置になる。
    """
    shape = pattern_shape()
    # "42" の左上の角を置ける範囲。外周から 1 セル空ける。
    max_left = width - PATTERN_WIDTH - 1
    max_top = height - PATTERN_HEIGHT - 1
    centre = ((width - PATTERN_WIDTH) // 2, (height - PATTERN_HEIGHT) // 2)
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
