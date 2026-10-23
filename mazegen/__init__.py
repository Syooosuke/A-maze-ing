"""標準ライブラリだけで動く、小さな迷路生成パッケージ。

長方形の迷路を作って解く。隣り合うセルの壁の情報が食い違わないように
する。迷路を作るクラスは MazeGenerator ひとつだけ。ほかに、例外
MazeError、壁の向きの定数（NORTH, EAST, SOUTH, WEST）、座標の型 Coord、
新しいシードを引く random_seed() を公開する。

使い方::

    from mazegen import MazeGenerator

    gen = MazeGenerator(width=21, height=15, seed=42)
    gen.generate()

    print(gen.grid[0])       # 1 行目（y=0）の各セルの、閉じている壁のビット
    print(gen.solution)      # [(0, 0), (1, 0), ...]
    print(gen.directions)    # 'EEESSSWS...'

主なコンストラクタ引数: width/height（格子の大きさ、2 以上 1000 以下）、
entry/exit（入口と出口の座標。省略すると左上と右下）、perfect（True
なら経路が 1 本の完全迷路。省略時の False なら、ループが 2 つ以上ある
Pac-Man 盤）、seed（省略するとランダム）。

大きさが範囲外、入口や出口が迷路の外、入口と出口が同じセル、2x2 で
perfect=False、型が違う値のときは MazeError を送出する。

generate() を呼んだ後は、grid（各セルの閉じた壁のビット。NORTH=1,
EAST=2, SOUTH=4, WEST=8）、solution（入口から出口への最短経路）、
directions（同じ経路を N/E/S/W で表した文字列）、pattern_cells（「42」の
セルの集合）、pattern_warning（「42」を描けなかった理由。描けたら
None）、seed_used（実際に使ったシード）から結果を読める。check() は
要件を満たしていない点のリストを返す。

ライセンス: MIT（全文はリポジトリの LICENSE.md と、wheel の dist-info にある）。
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
