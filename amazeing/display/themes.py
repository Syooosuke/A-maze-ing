"""迷路の配色。メニューの 3 で、壁を含む全体の配色が順に切り替わる。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Theme:
    """名前付きの配色。色は xterm の 256 色番号（0〜255）で持つ。

    Attributes:
        name: 画面下の要約の行に表示する名前。
        wall: 壁の色。
        pattern: "42" のパターンの色。
        path: 最短経路の色。
        entry: 入口の色。
        exit: 出口の色。
    """

    name: str
    wall: int
    pattern: int
    path: int
    entry: int
    exit: int


# メニューの「壁の色を変える」で、この順に切り替わる。
THEMES: Tuple[Theme, ...] = (
    Theme("classic", wall=250, pattern=189, path=51, entry=201, exit=196),
    Theme("amber", wall=214, pattern=229, path=45, entry=201, exit=196),
    Theme("emerald", wall=41, pattern=194, path=105, entry=213, exit=202),
    Theme("ocean", wall=39, pattern=195, path=226, entry=201, exit=196),
)
