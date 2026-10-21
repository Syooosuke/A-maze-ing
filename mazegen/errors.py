"""mazegen が送出する例外。"""

from __future__ import annotations


class MazeError(Exception):
    """迷路を作れない、または迷路の操作に失敗したときに送出する。

    例: 引数が不正、経路ができない、隣り合わないセルの並びを向きに変える。
    """
