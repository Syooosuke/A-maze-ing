"""迷路の定数と、新しいシードを引く random_seed()。

壁のビット、向きとその文字、大きさの範囲、ループと行き止まりの数、
シードの範囲を定める。
"""

from __future__ import annotations

import random
from typing import Dict, Tuple, TypeAlias

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
Coord: TypeAlias = Tuple[int, int]

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
# 変えるときは、README.md / README.ja.md と mazegen/__init__.py に書いた
# 「1000」も直す。
MAX_SIZE: int = 1000

# Pac-Man 盤（PERFECT=False）に必要な、独立したループの最小数。
MIN_LOOPS: int = 2

# Pac-Man 盤で許す行き止まりの数。subject は "a couple are tolerated" とだけ
# 書いているので、maze_analyzer.py の既定値（--max-dead-ends 2）に合わせた。
MAX_DEAD_ENDS: int = 2

# random_seed() が引くシードは 32 ビットに収める。設定ファイルへ書き写して
# 再現しやすくするため（利用者が指定するシードは、どんな整数でもよい）。
SEED_LIMIT: int = 2 ** 32


def random_seed() -> int:
    """迷路を作り直すたびに引く、新しいシード値を返す。"""
    return random.randrange(SEED_LIMIT)
