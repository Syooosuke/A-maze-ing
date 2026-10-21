"""MazeGenerator に渡された条件の検証。"""

from __future__ import annotations

from .constants import ALGORITHMS, MAX_SIZE, MIN_SIZE, Coord
from .errors import MazeError
from .glyphs import GLYPHS


def check_arguments(
    width: int, height: int, entry: Coord, exit: Coord, algorithm: str,
    pattern_text: str,
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
    if algorithm not in ALGORITHMS:
        known = ", ".join(ALGORITHMS)
        raise MazeError(f"unknown algorithm {algorithm!r} (known: {known})")
    for char in pattern_text:
        if char not in GLYPHS:
            raise MazeError(f"no glyph available for {char!r}")
    for label, (x, y) in (("ENTRY", entry), ("EXIT", exit)):
        if not (0 <= x < width and 0 <= y < height):
            raise MazeError(
                f"{label} {x},{y} is outside the {width}x{height} maze"
            )
    if entry == exit:
        raise MazeError("entry and exit must be different cells")
