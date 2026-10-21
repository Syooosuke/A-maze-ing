"""mazegen -- 依存関係のない小さな迷路生成モジュール。

長方形の迷路を作り、解いて、壁の対応関係が崩れないように保つ。公開する
クラスは MazeGenerator ひとつだけ。

使い方::

    from mazegen import MazeGenerator

    gen = MazeGenerator(width=21, height=15, seed=42)
    gen.generate()

    print(gen.grid[0])       # 1 行目の壁ビットマスク
    print(gen.solution)      # [(0, 0), (1, 0), ...]
    print(gen.directions)    # 'ESSEEN...'

主なコンストラクタ引数: width/height（格子の大きさ、2 以上）、
entry/exit（入口と出口の座標。exit の既定値は右下）、perfect（True
なら経路が 1 本の完全迷路、False ならループのある編み込み盤）、seed
（再現用のシード）。

generate() を呼んだ後は、grid（各セルの壁ビットマスク。NORTH=1,
EAST=2, SOUTH=4, WEST=8）、solution（入口から出口への最短経路）、
directions（同じ経路を N/E/S/W で表した文字列）、pattern_cells（描いた
パターンのセル集合）、seed_used（実際に使ったシード）から結果を読める。

ライセンス: MIT -- LICENSE.md を参照。
"""

from __future__ import annotations

from .constants import (
    Coord,
    EAST,
    NORTH,
    SOUTH,
    WEST,
    random_seed,
)
from .errors import MazeError
from .generator import MazeGenerator

__version__ = "1.0.0"

__all__ = [
    "Coord",
    "EAST",
    "MazeError",
    "MazeGenerator",
    "NORTH",
    "SOUTH",
    "WEST",
    "random_seed",
]
