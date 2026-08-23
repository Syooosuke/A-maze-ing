"""壁のビット、向き、大きさの上限といった定数。"""

from __future__ import annotations

import random
from typing import Dict, Tuple


NORTH: int = 1

EAST: int = 2

SOUTH: int = 4

WEST: int = 8

ALL_WALLS: int = NORTH | EAST | SOUTH | WEST

Coord = Tuple[int, int]

ALGORITHMS: Tuple[str, ...] = ("backtracker", "prim", "kruskal")

# 迷路の一辺として認める大きさ。設定ファイルの検証も同じ値を使う。
MIN_SIZE: int = 2

MAX_SIZE: int = 1000

# シードは 32 ビットに収める。再現用に設定ファイルへ書き写しやすい。
_SEED_LIMIT = 2 ** 32

_DIRECTIONS: Tuple[int, ...] = (NORTH, EAST, SOUTH, WEST)

_DELTA: Dict[int, Coord] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

_OPPOSITE: Dict[int, int] = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}

_LETTER: Dict[int, str] = {NORTH: "N", EAST: "E", SOUTH: "S", WEST: "W"}

# 1 歩ぶんの移動から向きの文字を引くための逆引き表。
_STEP_LETTER: Dict[Coord, str] = {
    _DELTA[direction]: letter for direction, letter in _LETTER.items()
}


def random_seed() -> int:
    """迷路を作り直すたびに引く、新しいシード値を返す。"""
    return random.randrange(_SEED_LIMIT)
