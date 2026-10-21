"""壁のビット、向き、大きさの範囲、ループの数といった定数と、新しい
シードを引く random_seed()。"""

from __future__ import annotations

import random
from typing import Dict, Tuple

# セル 1 つの壁は 4 ビットで表す。ビットが 1 なら、その向きの壁が閉じている。
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
ALL_WALLS: int = NORTH | EAST | SOUTH | WEST

# 4 つの向きを調べる順番。乱数の引き方に影響するので、順番を変えると
# 同じシードでも別の迷路になる。
DIRECTIONS: Tuple[int, ...] = (NORTH, EAST, SOUTH, WEST)

# 座標は (x, y)。x は右へ、y は下へ増える。
Coord = Tuple[int, int]

# その向きへ 1 歩進んだときの (dx, dy)。
DELTA: Dict[int, Coord] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

# 壁の反対側のセルから見た、同じ壁の向き。
OPPOSITE: Dict[int, int] = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}

# 出力ファイルで経路を書くときの文字。
LETTER: Dict[int, str] = {NORTH: "N", EAST: "E", SOUTH: "S", WEST: "W"}

# 迷路の一辺として認める大きさ。MazeGenerator の引数の検証で使う。
MIN_SIZE: int = 2
MAX_SIZE: int = 1000

# Pac-Man 盤（PERFECT=False）に必要な、独立したループの最小数。
MIN_LOOPS: int = 2

# Pac-Man 盤で許す行き止まりの数（subject は「2 つ程度までなら許容」）。
MAX_DEAD_ENDS: int = 2

# シードは 32 ビットに収める。再現用に設定ファイルへ書き写しやすい。
SEED_LIMIT: int = 2 ** 32


def random_seed() -> int:
    """迷路を作り直すたびに引く、新しいシード値を返す。"""
    return random.randrange(SEED_LIMIT)
