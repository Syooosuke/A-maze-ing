"""生成した迷路が subject の要件を満たしているかを確かめる。"""

from __future__ import annotations

from typing import List, Set

from .routes import count_components, dead_ends, loop_count
from ..constants import ALL_WALLS, EAST, NORTH, OPPOSITE, SOUTH, WEST, Coord
from ..grid import Grid
from ..generation.pattern import landmarks


def find_problems(
    grid: Grid, region: List[Coord], pattern_cells: Set[Coord],
    perfect: bool,
) -> List[str]:
    """迷路が満たしていない要件を、読める文で列挙する。

    Returns:
        見つかった問題点。すべて満たしていれば空のリスト。
    """
    problems: List[str] = []
    problems += _check_borders(grid)
    problems += _check_shared_walls(grid)
    problems += _check_pattern_closed(grid, pattern_cells)
    problems += _check_no_3x3_area(grid)
    if count_components(grid, region) != 1:
        problems.append(
            "the corridors are not fully connected: some cells are isolated"
        )
    elif perfect:
        if loop_count(grid, region) != 0:
            problems.append("a perfect maze must not contain any loop")
    else:
        problems += _check_playable(grid, region, pattern_cells)
    return problems


def _check_borders(grid: Grid) -> List[str]:
    """外周の壁がすべて閉じているかを確かめる。"""
    problems: List[str] = []
    for x in range(grid.width):
        top, bottom = (x, 0), (x, grid.height - 1)
        if not grid.has_wall(top, NORTH):
            problems.append(f"cell {x},0 opens through the north border")
        if not grid.has_wall(bottom, SOUTH):
            problems.append(
                f"cell {x},{grid.height - 1} opens through the south border"
            )
    for y in range(grid.height):
        left, right = (0, y), (grid.width - 1, y)
        if not grid.has_wall(left, WEST):
            problems.append(f"cell 0,{y} opens through the west border")
        if not grid.has_wall(right, EAST):
            problems.append(
                f"cell {grid.width - 1},{y} opens through the east border"
            )
    return problems


def _check_shared_walls(grid: Grid) -> List[str]:
    """隣り合う 2 セルが、間の壁について同じ答えを持っているかを確かめる。"""
    problems: List[str] = []
    for cell in grid.cells():
        for direction in (EAST, SOUTH):
            other = grid.neighbour(cell, direction)
            if not grid.in_bounds(other):
                continue
            if grid.has_wall(cell, direction) != grid.has_wall(
                other, OPPOSITE[direction]
            ):
                problems.append(
                    f"cells {cell[0]},{cell[1]} and {other[0]},{other[1]} "
                    "disagree on their shared wall"
                )
    return problems


def _check_pattern_closed(grid: Grid, pattern_cells: Set[Coord]) -> List[str]:
    """"42" のセルが 4 枚の壁ですべて閉じているかを確かめる。"""
    return [
        f"pattern cell {x},{y} is not fully closed"
        for x, y in sorted(pattern_cells)
        if grid.walls[y][x] != ALL_WALLS
    ]


def _check_no_3x3_area(grid: Grid) -> List[str]:
    """壁のない 3x3 の区画がないかを確かめる（通路の幅は 2 セルまで）。"""
    return [
        f"the 3x3 area at {x},{y} is completely open"
        for y in range(grid.height - 2)
        for x in range(grid.width - 2)
        if grid.is_block_open(x, y, 3, 3)
    ]


def _check_playable(
    grid: Grid, region: List[Coord], pattern_cells: Set[Coord]
) -> List[str]:
    """Pac-Man 盤（PERFECT=False）にだけ求められる規則を確かめる。"""
    problems: List[str] = []
    if loop_count(grid, region) < 2:
        problems.append(
            "a playable board needs at least two independent routes"
        )
    for name, cell in landmarks(grid.width, grid.height).items():
        if cell in pattern_cells or grid.degree(cell) == 0:
            problems.append(f"the {name} is not an open corridor")
    ends = dead_ends(grid, region)
    # subject は「行き止まりは 2 つ程度までなら許容」としている。
    if len(ends) > 2:
        listed = ", ".join(f"{x},{y}" for x, y in ends[:5])
        problems.append(
            f"a playable board should not keep {len(ends)} "
            f"dead-ends ({listed}...)"
        )
    return problems
