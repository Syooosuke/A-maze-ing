"""MazeGenerator に渡された条件の検証。"""

from __future__ import annotations

from typing import Optional

from .constants import MAX_SIZE, MIN_LOOPS, MIN_SIZE, Coord
from .errors import MazeError


def check_types(
    width: int, height: int, entry: Coord, exit: Optional[Coord]
) -> None:
    """引数の型が違えば MazeError を送出する（"20" や [0, 0] など）。

    型の誤りも、ほかの誤りと同じ MazeError で知らせるため。exit は省略
    （None）してよい。
    """
    if not _is_int(width) or not _is_int(height):
        raise MazeError("width and height must be integers")
    for label, cell in (("ENTRY", entry), ("EXIT", exit)):
        if label == "EXIT" and cell is None:
            continue
        if not (
            isinstance(cell, tuple) and len(cell) == 2
            and _is_int(cell[0]) and _is_int(cell[1])
        ):
            raise MazeError(f"{label} must be a pair of integers (x, y)")


def check_arguments(
    width: int, height: int, entry: Coord, exit: Coord, perfect: bool
) -> None:
    """迷路を作れない条件なら、理由を添えて MazeError を送出する。"""
    if width < MIN_SIZE or height < MIN_SIZE:
        raise MazeError(
            f"maze size must be at least {MIN_SIZE}x{MIN_SIZE} cells"
        )
    if width > MAX_SIZE or height > MAX_SIZE:
        raise MazeError(
            f"maze size must not exceed {MAX_SIZE}x{MAX_SIZE} cells"
        )
    for label, (x, y) in (("ENTRY", entry), ("EXIT", exit)):
        if not (0 <= x < width and 0 <= y < height):
            raise MazeError(
                f"{label}: {x},{y} is outside the {width}x{height} maze"
            )
    if entry == exit:
        raise MazeError("ENTRY and EXIT must be different cells")
    # 2x2 の格子には壁が 4 枚しかなく、ループは最大 1 つしか作れない。
    # Pac-Man 盤（PERFECT=False）は独立したループを MIN_LOOPS 個以上必要とする。
    if not perfect and width == 2 and height == 2:
        raise MazeError(
            "a 2x2 maze is too small for a playable board "
            f"(PERFECT=False needs at least {MIN_LOOPS} independent loops)"
        )


def _is_int(value: object) -> bool:
    """value が整数かを返す。True / False は整数として扱わない。"""
    return isinstance(value, int) and not isinstance(value, bool)
