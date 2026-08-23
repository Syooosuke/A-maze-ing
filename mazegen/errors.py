"""mazegen が送出する例外。"""

from __future__ import annotations


class MazeError(Exception):
    """与えられた引数では迷路を作れないときに送出する。"""
