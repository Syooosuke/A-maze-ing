"""MazeGenerator に渡された条件の検証。"""

from __future__ import annotations

from .constants import MAX_SIZE, MIN_SIZE, Coord
from .errors import MazeError


def check_arguments(
    width: int, height: int, entry: Coord, exit: Coord
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
                f"{label} {x},{y} is outside the {width}x{height} maze"
            )
    if entry == exit:
        raise MazeError("entry and exit must be different cells")
