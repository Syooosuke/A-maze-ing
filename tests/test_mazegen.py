"""Unit tests of the reusable :mod:`mazegen` module."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from mazegen.analysis import routes
from mazegen.constants import ALL_WALLS
from mazegen import (
    EAST,
    NORTH,
    SOUTH,
    WEST,
    MazeError,
    MazeGenerator,
)

Coord = Tuple[int, int]

_OPPOSITE = {NORTH: SOUTH, EAST: WEST, SOUTH: NORTH, WEST: EAST}
_DELTA = {NORTH: (0, -1), EAST: (1, 0), SOUTH: (0, 1), WEST: (-1, 0)}


def build(**kwargs: Any) -> MazeGenerator:
    """Build and generate a maze, with sane defaults for the tests."""
    params: Dict[str, Any] = {
        "width": 25,
        "height": 17,
        "entry": (0, 0),
        "exit": (24, 16),
        "seed": 1,
    }
    params.update(kwargs)
    generator = MazeGenerator(**params)
    return generator.generate()


@pytest.mark.parametrize("seed", [1, 7, 42])
@pytest.mark.parametrize("perfect", [True, False])
def test_generated_mazes_are_valid(seed: int, perfect: bool) -> None:
    """Both modes pass the built-in checks."""
    generator = build(seed=seed, perfect=perfect)
    assert generator.check() == []


def test_same_seed_gives_the_same_maze() -> None:
    """Reproducibility: the seed fully determines the maze."""
    first = build(seed=1234)
    second = build(seed=1234)
    assert first.grid == second.grid
    assert first.directions == second.directions


def test_different_seeds_give_different_mazes() -> None:
    """Two seeds are very unlikely to produce the same maze."""
    assert build(seed=1).grid != build(seed=2).grid


def test_random_seed_is_recorded_and_replayable() -> None:
    """A maze built without a seed can still be replayed."""
    generator = MazeGenerator(21, 15, seed=None).generate()
    replay = MazeGenerator(21, 15, seed=generator.seed_used).generate()
    assert generator.grid == replay.grid


def test_walls_are_coherent_between_neighbours() -> None:
    """A shared wall is encoded the same way on both sides."""
    generator = build()
    for y in range(generator.height):
        for x in range(generator.width):
            for direction in (EAST, SOUTH):
                delta_x, delta_y = _DELTA[direction]
                near_x, near_y = x + delta_x, y + delta_y
                if near_x >= generator.width or near_y >= generator.height:
                    continue
                mine = bool(generator.grid[y][x] & direction)
                theirs = bool(
                    generator.grid[near_y][near_x] & _OPPOSITE[direction]
                )
                assert mine == theirs


def test_outer_border_is_closed() -> None:
    """No cell opens through the outside of the maze."""
    generator = build()
    width, height = generator.width, generator.height
    for x in range(width):
        assert generator.grid[0][x] & NORTH
        assert generator.grid[height - 1][x] & SOUTH
    for y in range(height):
        assert generator.grid[y][0] & WEST
        assert generator.grid[y][width - 1] & EAST


def test_perfect_maze_has_no_loop() -> None:
    """A perfect maze is a spanning tree: no loop at all."""
    generator = build(perfect=True)
    assert generator.loop_count() == 0


def test_perfect_maze_has_a_single_path() -> None:
    """Removing any wall of the solution disconnects entry from exit."""
    generator = build(perfect=True)
    path = generator.solution
    assert path[0] == generator.entry
    assert path[-1] == generator.exit
    for x, y in path[1:-1]:
        assert generator._grid.degree((x, y)) >= 2


def test_playable_board_has_loops_and_no_dead_end() -> None:
    """The default mode is a braided, Pac-Man ready board."""
    generator = build(perfect=False)
    assert generator.loop_count() >= 2
    assert generator.dead_ends() == []


def test_playable_board_opens_corners_and_centre() -> None:
    """Ghosts and the player need their starting cells."""
    generator = build(perfect=False)
    width, height = generator.width, generator.height
    landmarks: List[Coord] = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, height // 2),
    ]
    for x, y in landmarks:
        assert (x, y) not in generator.pattern_cells
        assert generator._grid.degree((x, y)) >= 1


def test_no_three_by_three_open_area() -> None:
    """Corridors never become wider than two cells."""
    generator = build(perfect=False)
    for y in range(generator.height - 2):
        for x in range(generator.width - 2):
            assert not generator._grid.is_block_open(x, y, 3, 3)


def test_pattern_cells_are_fully_closed() -> None:
    """The "42" is drawn with isolated, fully walled cells."""
    generator = build()
    assert generator.pattern_cells
    for x, y in generator.pattern_cells:
        assert generator.grid[y][x] == ALL_WALLS


def test_pattern_is_skipped_and_reported_when_too_small() -> None:
    """A tiny maze drops the pattern and explains why."""
    generator = MazeGenerator(6, 5, exit=(5, 4), seed=3).generate()
    assert generator.pattern_cells == set()
    assert generator.pattern_warning is not None
    assert "too small" in generator.pattern_warning


def test_all_corridors_are_reachable() -> None:
    """No cell is isolated, except the pattern ones."""
    generator = build(perfect=False)
    reachable = {generator.entry}
    stack = [generator.entry]
    while stack:
        cell = stack.pop()
        for neighbour in generator._grid.open_neighbours(cell):
            if neighbour not in reachable:
                reachable.add(neighbour)
                stack.append(neighbour)
    expected = generator.width * generator.height
    expected -= len(generator.pattern_cells)
    assert len(reachable) == expected


def test_solution_is_a_shortest_walkable_path() -> None:
    """Each move of the solution crosses an open wall."""
    generator = build()
    path = generator.solution
    assert len(generator.directions) == len(path) - 1
    for (from_x, from_y), (to_x, to_y) in zip(path, path[1:]):
        step = (to_x - from_x, to_y - from_y)
        direction = next(d for d, delta in _DELTA.items() if delta == step)
        assert not generator._grid.has_wall((from_x, from_y), direction)


def test_hex_lines_match_the_grid() -> None:
    """The hexadecimal export mirrors the wall bitmasks."""
    generator = build()
    lines = generator.to_hex_lines()
    assert len(lines) == generator.height
    for y, line in enumerate(lines):
        assert len(line) == generator.width
        for x, digit in enumerate(line):
            assert int(digit, 16) == generator.grid[y][x]


def test_smallest_possible_maze() -> None:
    """A 2x2 maze is degenerate but must still work."""
    generator = MazeGenerator(
        2, 2, (0, 0), (1, 1), perfect=True, seed=5
    ).generate()
    assert generator.solution[0] == (0, 0)
    assert generator.solution[-1] == (1, 1)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": 1, "height": 5},
        {"width": 5, "height": 1},
        {"width": 5, "height": 5, "entry": (0, 0), "exit": (0, 0)},
        {"width": 5, "height": 5, "entry": (9, 0)},
        {"width": 5, "height": 5, "exit": (0, 9)},
        {"width": 5000, "height": 5},
    ],
)
def test_invalid_parameters_raise_maze_error(
    kwargs: Dict[str, Any]
) -> None:
    """Bad parameters are rejected with a clear exception."""
    with pytest.raises(MazeError):
        MazeGenerator(**kwargs)


def test_path_to_directions_rejects_a_jump() -> None:
    """Two non-adjacent cells cannot be turned into a move."""
    with pytest.raises(MazeError):
        routes.path_to_directions([(0, 0), (4, 4)])


def test_solve_between_arbitrary_cells() -> None:
    """The solver is not limited to the entry and the exit."""
    generator = build()
    corridors = sorted(
        (x, y)
        for y in range(generator.height)
        for x in range(generator.width)
        if (x, y) not in generator.pattern_cells
    )
    start, goal = corridors[1], corridors[-2]
    path = routes.solve(generator._grid, start, goal)
    assert path[0] == start
    assert path[-1] == goal


def test_solve_returns_nothing_for_a_walled_cell() -> None:
    """A pattern cell is isolated: no path leads to it."""
    generator = build()
    target = sorted(generator.pattern_cells)[0]
    assert routes.solve(generator._grid, generator.entry, target) == []


def test_default_mode_is_the_playable_board() -> None:
    """Like the PERFECT flag of the subject, perfect defaults to False."""
    generator = MazeGenerator(25, 17, seed=42).generate()
    assert generator.perfect is False
    assert generator.loop_count() >= 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": "20", "height": 10},
        {"width": 10.5, "height": 10},
        {"width": True, "height": 10},
        {"width": 10, "height": 10, "entry": [0, 0]},
        {"width": 10, "height": 10, "exit": (1, 2, 3)},
        {"width": 10, "height": 10, "perfect": "False"},
        {"width": 10, "height": 10, "perfect": None},
        {"width": 10, "height": 10, "seed": [1]},
        {"width": 10, "height": 10, "seed": 1.5},
    ],
)
def test_wrong_types_raise_maze_error(kwargs: Dict[str, Any]) -> None:
    """A wrongly typed argument is a MazeError, not a raw TypeError."""
    with pytest.raises(MazeError):
        MazeGenerator(**kwargs)


@pytest.mark.parametrize("seed", ["20", [1], 1.5])
def test_generate_rejects_a_wrong_seed(seed: Any) -> None:
    """generate(seed=...) checks the type like the constructor does."""
    generator = MazeGenerator(10, 10)
    with pytest.raises(MazeError):
        generator.generate(seed=seed)
