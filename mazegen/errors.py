"""mazegen が送出する例外。"""

from __future__ import annotations


class MazeError(Exception):
    """迷路を作れないとき（引数が不正、経路ができない）や、迷路の操作に
    失敗したとき（隣り合わないセルの並びを向きに変える）に送出する。
    """
