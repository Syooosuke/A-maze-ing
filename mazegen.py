"""mazegen -- a small, dependency-free maze generator.

This module is the reusable part of the *A-Maze-ing* project.  It exposes a
single class, :class:`MazeGenerator`, which builds rectangular mazes, keeps
them coherent (a wall is always encoded the same way by both cells sharing
it) and can solve them.

Installation
------------
The module is shipped as a standard Python package::

    pip install mazegen-1.0.0-py3-none-any.whl

Quick start
-----------
::

    from mazegen import MazeGenerator

    gen = MazeGenerator(width=21, height=15, seed=42)
    gen.generate()

    print(gen.grid[0])           # wall bitmasks of the first row
    print(gen.solution)          # [(0, 0), (1, 0), ...]
    print(gen.directions)        # 'ESSEEN...'
    print("\\n".join(gen.to_hex_lines()))

Custom parameters
-----------------
``MazeGenerator`` accepts:

======================  ====================================================
``width``, ``height``   Size of the grid, in cells (>= 2).
``entry``, ``exit``     ``(x, y)`` coordinates; must differ and be in bounds.
                        ``exit`` defaults to the bottom-right cell.
``perfect``             ``True``  -> exactly one path between entry and exit.
                        ``False`` -> braided, Pac-Man like board with loops.
``seed``                ``int`` for reproducible mazes, ``None`` for random.
                        The seed actually used is kept in ``seed_used``.
``algorithm``           One of :data:`ALGORITHMS`: ``'backtracker'``,
                        ``'prim'`` or ``'kruskal'``.
``pattern``             Draw the ``'42'`` pattern with fully closed cells.
``pattern_text``        Text drawn by the pattern (digits ``'4'``/``'2'``).
======================  ====================================================

Accessing the generated structure
---------------------------------
After :meth:`MazeGenerator.generate`:

``grid``
    ``List[List[int]]`` indexed as ``grid[y][x]``.  Each value is a bitmask
    of the **closed** walls: :data:`NORTH` (1), :data:`EAST` (2),
    :data:`SOUTH` (4), :data:`WEST` (8).
``pattern_cells``
    ``Set[Tuple[int, int]]`` -- the fully closed cells drawing the ``42``.
``pattern_warning``
    ``Optional[str]`` -- why the pattern could not be drawn, if it was not.
``solution``
    ``List[Tuple[int, int]]`` -- shortest path from entry to exit.
``directions``
    ``str`` -- the same path as ``N`` / ``E`` / ``S`` / ``W`` letters.
``seed_used``
    ``int`` -- seed of the last generation, replay it to get the same maze.

Useful methods: :meth:`MazeGenerator.is_open`,
:meth:`MazeGenerator.open_neighbours`, :meth:`MazeGenerator.solve`,
:meth:`MazeGenerator.to_hex_lines`, :meth:`MazeGenerator.dead_ends`,
:meth:`MazeGenerator.loop_count` and :meth:`MazeGenerator.check`.

Example -- reusing the generator in a game::

    gen = MazeGenerator(19, 15, perfect=False, seed=7).generate()
    for y, row in enumerate(gen.grid):
        for x, walls in enumerate(row):
            if (x, y) in gen.pattern_cells:
                board[y][x] = "wall"
            elif gen.is_open(x, y, EAST):
                board[y][x] = "corridor"

Licence: MIT -- see ``LICENSE.md`` in the project repository.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple

__version__ = "1.0.0"

__all__ = [
    "ALGORITHMS",
    "ALL_WALLS",
    "EAST",
    "MazeError",
    "MazeGenerator",
    "NORTH",
    "SOUTH",
    "WEST",
]


class MazeError(Exception):
    """Raised when a maze cannot be built with the given parameters."""


NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
ALL_WALLS: int = NORTH | EAST | SOUTH | WEST

Coord = Tuple[int, int]

ALGORITHMS: Tuple[str, ...] = ("backtracker", "prim", "kruskal")

_DIRECTIONS: Tuple[int, ...] = (NORTH, EAST, SOUTH, WEST)
_DELTA: Dict[int, Coord] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}
_OPPOSITE: Dict[int, int] = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}
_LETTER: Dict[int, str] = {NORTH: "N", EAST: "E", SOUTH: "S", WEST: "W"}

# Bitmap font used to draw the mandatory "42" pattern.  Every hole of a
# glyph is at least two cells thick: a one cell wide hole would be a pocket
# the braiding cannot open, and would leave a dead-end behind.
_GLYPHS: Dict[str, Tuple[str, ...]] = {
    "4": (
        "#  #",
        "#  #",
        "#  #",
        "####",
        "   #",
        "   #",
        "   #",
    ),
    "2": (
        "####",
        "   #",
        "   #",
        "####",
        "#   ",
        "#   ",
        "####",
    ),
}
_GLYPH_W = 4
_GLYPH_H = 7
_GLYPH_GAP = 1

# The pattern is never allowed to eat more than this share of the grid,
# otherwise the maze itself becomes too cramped to stay interesting.
_MAX_PATTERN_RATIO = 0.30


def _glyph_shape(text: str, scale: int) -> Tuple[Set[Coord], int, int]:
    """Return the cells of ``text`` drawn at ``scale``, plus its size.

    Args:
        text: Characters to draw; each one must exist in the bitmap font.
        scale: Zoom factor applied to every pixel of the font.

    Returns:
        A tuple ``(cells, width, height)`` where ``cells`` holds the
        coordinates of the drawn pixels, relative to the top-left corner.
    """
    cells: Set[Coord] = set()
    offset = 0
    for char in text:
        rows = _GLYPHS[char]
        for row_index, row in enumerate(rows):
            for col_index, mark in enumerate(row):
                if mark != "#":
                    continue
                base_x = offset + col_index * scale
                base_y = row_index * scale
                for dy in range(scale):
                    for dx in range(scale):
                        cells.add((base_x + dx, base_y + dy))
        offset += (_GLYPH_W + _GLYPH_GAP) * scale
    width = offset - _GLYPH_GAP * scale
    return cells, width, _GLYPH_H * scale


class MazeGenerator:
    """Build, braid and solve a rectangular maze.

    Walls are stored as a bitmask per cell, so a maze is nothing more than
    a ``List[List[int]]``.  Every wall is always written on both sides at
    once, which makes the structure coherent by construction.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Coord = (0, 0),
        exit: Optional[Coord] = None,
        perfect: bool = True,
        seed: Optional[int] = None,
        algorithm: str = "backtracker",
        pattern: bool = True,
        pattern_text: str = "42",
    ) -> None:
        """Validate the parameters and prepare an empty maze.

        Args:
            width: Number of columns, at least 2.
            height: Number of rows, at least 2.
            entry: ``(x, y)`` coordinates of the entrance.
            exit: ``(x, y)`` coordinates of the exit, bottom-right by
                default.
            perfect: Build a perfect maze instead of a braided board.
            seed: Seed making the generation reproducible.
            algorithm: Spanning tree algorithm, see :data:`ALGORITHMS`.
            pattern: Draw the "42" pattern with fully closed cells.
            pattern_text: Text drawn by the pattern.

        Raises:
            MazeError: If any parameter is out of range or inconsistent.
        """
        if width < 2 or height < 2:
            raise MazeError("maze size must be at least 2x2 cells")
        if width > 1000 or height > 1000:
            raise MazeError("maze size must not exceed 1000x1000 cells")
        if algorithm not in ALGORITHMS:
            known = ", ".join(ALGORITHMS)
            raise MazeError(
                f"unknown algorithm {algorithm!r} (known: {known})"
            )
        for char in pattern_text:
            if char not in _GLYPHS:
                raise MazeError(f"no glyph available for {char!r}")

        self.width: int = width
        self.height: int = height
        self.entry: Coord = entry
        self.exit: Coord = (
            (width - 1, height - 1) if exit is None else exit
        )
        self.perfect: bool = perfect
        self.seed: Optional[int] = seed
        self.algorithm: str = algorithm
        self.pattern: bool = pattern
        self.pattern_text: str = pattern_text

        self._check_endpoint(self.entry, "ENTRY")
        self._check_endpoint(self.exit, "EXIT")
        if self.entry == self.exit:
            raise MazeError("entry and exit must be different cells")

        self.grid: List[List[int]] = []
        self.pattern_cells: Set[Coord] = set()
        self.pattern_warning: Optional[str] = None
        self.solution: List[Coord] = []
        self.directions: str = ""
        self.seed_used: int = 0
        self._region: List[Coord] = []
        self._rng: random.Random = random.Random(seed)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate(self, seed: Optional[int] = None) -> "MazeGenerator":
        """Generate a brand new maze in place.

        Args:
            seed: Overrides the seed given to the constructor.  When both
                are ``None`` a random seed is drawn and stored in
                ``seed_used``.

        Returns:
            ``self``, so calls can be chained.

        Raises:
            MazeError: If the maze cannot be built (no path, empty grid).
        """
        base = seed if seed is not None else self.seed
        if base is None:
            base = random.randrange(2 ** 32)
        self.seed_used = base
        self._rng = random.Random(base)

        self.grid = [
            [ALL_WALLS] * self.width for _ in range(self.height)
        ]
        self.pattern_cells, self.pattern_warning = self._place_pattern()
        self._region = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self.pattern_cells
        ]
        if not self._region:
            raise MazeError("the pattern leaves no room for the maze")

        self._carve_spanning_tree()
        if not self.perfect:
            self._braid()
            self._add_loops(2)

        self.solution = self.solve()
        if not self.solution:
            raise MazeError("no path between the entry and the exit")
        self.directions = self.path_to_directions(self.solution)
        return self

    def _check_endpoint(self, cell: Coord, label: str) -> None:
        """Raise :class:`MazeError` if ``cell`` is outside the grid."""
        x, y = cell
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise MazeError(
                f"{label} {x},{y} is outside the "
                f"{self.width}x{self.height} maze"
            )

    # ------------------------------------------------------------------
    # The "42" pattern
    # ------------------------------------------------------------------
    def _place_pattern(self) -> Tuple[Set[Coord], Optional[str]]:
        """Choose where the "42" pattern fits, if it fits at all.

        Returns:
            The cells of the pattern and, when it had to be skipped, a
            message explaining why.
        """
        if not self.pattern or not self.pattern_text:
            return set(), None

        reserved = {
            self.entry,
            self.exit,
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
            (self.width // 2, self.height // 2),
        }
        budget = _MAX_PATTERN_RATIO * self.width * self.height
        span = len(self.pattern_text) * (_GLYPH_W + _GLYPH_GAP) - _GLYPH_GAP
        max_scale = min(
            (self.width - 2) // span,
            (self.height - 2) // _GLYPH_H,
        )
        for scale in range(max_scale, 0, -1):
            shape, shape_w, shape_h = _glyph_shape(self.pattern_text, scale)
            if len(shape) > budget:
                continue
            cells = self._fit_shape(shape, shape_w, shape_h, reserved)
            if cells is not None:
                return cells, None

        return set(), (
            f"the {self.pattern_text!r} pattern was skipped: a "
            f"{self.width}x{self.height} maze is too small for it "
            f"(at least {span + 2}x{_GLYPH_H + 2} cells are needed)"
        )

    def _fit_shape(
        self,
        shape: Set[Coord],
        shape_w: int,
        shape_h: int,
        reserved: Set[Coord],
    ) -> Optional[Set[Coord]]:
        """Try to place ``shape`` without breaking the maze.

        The pattern must keep a one cell margin with the borders, must not
        cover a reserved cell (entry, exit, corners, centre) and must leave
        every remaining cell reachable.

        Returns:
            The translated cells, or ``None`` when no placement works.
        """
        if shape_w + 2 > self.width or shape_h + 2 > self.height:
            return None
        max_x = self.width - shape_w - 1
        max_y = self.height - shape_h - 1
        offsets: List[Coord] = [
            (
                min(max(1, (self.width - shape_w) // 2), max_x),
                min(max(1, (self.height - shape_h) // 2), max_y),
            )
        ]
        for _ in range(25):
            offsets.append(
                (
                    self._rng.randint(1, max_x),
                    self._rng.randint(1, max_y),
                )
            )
        for off_x, off_y in offsets:
            cells = {(x + off_x, y + off_y) for x, y in shape}
            if cells & reserved:
                continue
            if self._leaves_connected_region(cells):
                return cells
        return None

    def _leaves_connected_region(self, blocked: Set[Coord]) -> bool:
        """Tell whether all cells outside ``blocked`` remain connected."""
        total = self.width * self.height - len(blocked)
        if total <= 0:
            return False
        start = next(
            (
                (x, y)
                for y in range(self.height)
                for x in range(self.width)
                if (x, y) not in blocked
            ),
            None,
        )
        if start is None:
            return False
        seen: Set[Coord] = {start}
        queue: deque[Coord] = deque([start])
        while queue:
            x, y = queue.popleft()
            for delta_x, delta_y in _DELTA.values():
                cell = (x + delta_x, y + delta_y)
                if not self._in_bounds(*cell):
                    continue
                if cell in blocked or cell in seen:
                    continue
                seen.add(cell)
                queue.append(cell)
        return len(seen) == total

    # ------------------------------------------------------------------
    # Spanning tree algorithms
    # ------------------------------------------------------------------
    def _carve_spanning_tree(self) -> None:
        """Carve a spanning tree over every cell outside the pattern."""
        if self.algorithm == "prim":
            self._carve_prim()
        elif self.algorithm == "kruskal":
            self._carve_kruskal()
        else:
            self._carve_backtracker()

    def _carve_backtracker(self) -> None:
        """Randomised depth-first search (recursive backtracker)."""
        start = self._rng.choice(self._region)
        visited: Set[Coord] = {start}
        stack: List[Coord] = [start]
        while stack:
            x, y = stack[-1]
            neighbours = {
                direction: self._step(x, y, direction)
                for direction in _DIRECTIONS
            }
            options = [
                direction
                for direction, cell in neighbours.items()
                if cell not in visited and self._is_corridor(*cell)
            ]
            if not options:
                stack.pop()
                continue
            direction = self._rng.choice(options)
            self._carve(x, y, direction)
            cell = neighbours[direction]
            visited.add(cell)
            stack.append(cell)

    def _carve_prim(self) -> None:
        """Randomised Prim algorithm."""
        start = self._rng.choice(self._region)
        visited: Set[Coord] = {start}
        frontier: List[Tuple[Coord, int]] = []
        self._push_frontier(start, visited, frontier)
        while frontier:
            index = self._rng.randrange(len(frontier))
            (x, y), direction = frontier.pop(index)
            cell = self._step(x, y, direction)
            if cell in visited:
                continue
            self._carve(x, y, direction)
            visited.add(cell)
            self._push_frontier(cell, visited, frontier)

    def _push_frontier(
        self,
        cell: Coord,
        visited: Set[Coord],
        frontier: List[Tuple[Coord, int]],
    ) -> None:
        """Record the walls of ``cell`` leading to unvisited corridors."""
        x, y = cell
        for direction in _DIRECTIONS:
            neighbour = self._step(x, y, direction)
            if self._is_corridor(*neighbour) and neighbour not in visited:
                frontier.append((cell, direction))

    def _corridor_edges(self) -> Iterator[Tuple[Coord, int]]:
        """Yield every wall shared by two corridor cells, once each.

        Only the east and south walls are looked at, so the wall between
        two cells is reported by the northern or western one only.
        """
        for x, y in self._region:
            for direction in (EAST, SOUTH):
                if self._is_corridor(*self._step(x, y, direction)):
                    yield (x, y), direction

    def _carve_kruskal(self) -> None:
        """Randomised Kruskal algorithm, using a union-find structure."""
        edges: List[Tuple[Coord, int]] = list(self._corridor_edges())
        self._rng.shuffle(edges)
        parent: Dict[Coord, Coord] = {cell: cell for cell in self._region}

        def find(cell: Coord) -> Coord:
            root = cell
            while parent[root] != root:
                root = parent[root]
            while parent[cell] != root:
                parent[cell], cell = root, parent[cell]
            return root

        for (x, y), direction in edges:
            left = find((x, y))
            right = find(self._step(x, y, direction))
            if left == right:
                continue
            parent[left] = right
            self._carve(x, y, direction)

    # ------------------------------------------------------------------
    # Braiding (Pac-Man mode)
    # ------------------------------------------------------------------
    def _braid(self) -> None:
        """Remove dead-ends by opening extra walls.

        A wall is only removed when it does not create a 3x3 fully open
        area, so corridors never become wider than two cells.
        """
        while True:
            ends = [
                cell for cell in self._region if self.degree(*cell) <= 1
            ]
            if not ends:
                return
            self._rng.shuffle(ends)
            progress = False
            for x, y in ends:
                if self.degree(x, y) > 1:
                    continue
                options = self._openable_walls(x, y)
                if not options:
                    continue
                self._rng.shuffle(options)
                options.sort(
                    key=lambda d: self.degree(*self._step(x, y, d))
                )
                self._carve(x, y, options[0])
                progress = True
            if not progress:
                return

    def _openable_walls(self, x: int, y: int) -> List[int]:
        """List the walls of ``(x, y)`` that may safely be removed."""
        options: List[int] = []
        for direction in _DIRECTIONS:
            if not self.grid[y][x] & direction:
                continue
            if not self._is_corridor(*self._step(x, y, direction)):
                continue
            if self._creates_open_block(x, y, direction):
                continue
            options.append(direction)
        return options

    def _add_loops(self, target: int) -> None:
        """Open extra walls until the maze holds ``target`` loops."""
        loops = self.loop_count()
        if loops >= target:
            return
        candidates: List[Tuple[Coord, int]] = [
            ((x, y), direction)
            for (x, y), direction in self._corridor_edges()
            if self.grid[y][x] & direction
        ]
        self._rng.shuffle(candidates)
        for (x, y), direction in candidates:
            if loops >= target:
                return
            if not self.grid[y][x] & direction:
                continue
            if self._creates_open_block(x, y, direction):
                continue
            self._carve(x, y, direction)
            loops += 1

    # ------------------------------------------------------------------
    # Low level wall helpers
    # ------------------------------------------------------------------
    def _in_bounds(self, x: int, y: int) -> bool:
        """Tell whether ``(x, y)`` belongs to the grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def _is_corridor(self, x: int, y: int) -> bool:
        """Tell whether ``(x, y)`` is a cell the maze may dig through."""
        return self._in_bounds(x, y) and (x, y) not in self.pattern_cells

    @staticmethod
    def _step(x: int, y: int, direction: int) -> Coord:
        """Return the neighbour of ``(x, y)`` in ``direction``."""
        delta_x, delta_y = _DELTA[direction]
        return x + delta_x, y + delta_y

    def _carve(self, x: int, y: int, direction: int) -> None:
        """Open the wall between ``(x, y)`` and its neighbour."""
        other_x, other_y = self._step(x, y, direction)
        self.grid[y][x] &= ~direction
        self.grid[other_y][other_x] &= ~_OPPOSITE[direction]

    def _close(self, x: int, y: int, direction: int) -> None:
        """Close the wall between ``(x, y)`` and its neighbour."""
        other_x, other_y = self._step(x, y, direction)
        self.grid[y][x] |= direction
        self.grid[other_y][other_x] |= _OPPOSITE[direction]

    def _creates_open_block(self, x: int, y: int, direction: int) -> bool:
        """Tell whether opening a wall would create a 3x3 open area."""
        other_x, other_y = self._step(x, y, direction)
        self._carve(x, y, direction)
        found = self._open_block_around(x, y, other_x, other_y)
        self._close(x, y, direction)
        return found

    def _open_block_around(
        self, x: int, y: int, other_x: int, other_y: int
    ) -> bool:
        """Look for a 3x3 open area containing both given cells."""
        low_x, high_x = min(x, other_x), max(x, other_x)
        low_y, high_y = min(y, other_y), max(y, other_y)
        xs = range(max(0, high_x - 2), min(low_x, self.width - 3) + 1)
        ys = range(max(0, high_y - 2), min(low_y, self.height - 3) + 1)
        for block_y in ys:
            for block_x in xs:
                if self.is_block_open(block_x, block_y, 3, 3):
                    return True
        return False

    def is_block_open(
        self, x: int, y: int, width: int, height: int
    ) -> bool:
        """Tell whether a rectangle of cells has no inner wall left.

        Args:
            x: Left column of the rectangle.
            y: Top row of the rectangle.
            width: Width of the rectangle, in cells.
            height: Height of the rectangle, in cells.

        Returns:
            ``True`` when every wall inside the rectangle is open.
        """
        if x + width > self.width or y + height > self.height:
            return False
        for row in range(y, y + height):
            for col in range(x, x + width):
                walls = self.grid[row][col]
                if col + 1 < x + width and walls & EAST:
                    return False
                if row + 1 < y + height and walls & SOUTH:
                    return False
        return True

    # ------------------------------------------------------------------
    # Public inspection helpers
    # ------------------------------------------------------------------
    def walls_at(self, x: int, y: int) -> int:
        """Return the bitmask of the closed walls of cell ``(x, y)``."""
        return self.grid[y][x]

    def is_open(self, x: int, y: int, direction: int) -> bool:
        """Tell whether the wall of ``(x, y)`` in ``direction`` is open."""
        return not self.grid[y][x] & direction

    def open_neighbours(self, x: int, y: int) -> Iterator[Coord]:
        """Yield the cells reachable from ``(x, y)`` in one step."""
        for direction in _DIRECTIONS:
            if self.grid[y][x] & direction:
                continue
            neighbour = self._step(x, y, direction)
            if self._in_bounds(*neighbour):
                yield neighbour

    def degree(self, x: int, y: int) -> int:
        """Return how many walls of ``(x, y)`` are open."""
        return sum(
            1 for direction in _DIRECTIONS if not self.grid[y][x] & direction
        )

    def dead_ends(self) -> List[Coord]:
        """Return the corridor cells having a single open wall."""
        return [cell for cell in self._region if self.degree(*cell) == 1]

    def loop_count(self) -> int:
        """Return the number of independent loops (cyclomatic number)."""
        edges = 0
        for x, y in self._region:
            for direction in (EAST, SOUTH):
                if not self.grid[y][x] & direction:
                    edges += 1
        return edges - len(self._region) + self._component_count()

    def _reachable_from(self, start: Coord) -> Set[Coord]:
        """Return every cell connected to ``start`` by open walls."""
        seen: Set[Coord] = {start}
        queue: deque[Coord] = deque([start])
        while queue:
            for neighbour in self.open_neighbours(*queue.popleft()):
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return seen

    def _component_count(self) -> int:
        """Count the connected groups of corridor cells."""
        seen: Set[Coord] = set()
        components = 0
        for cell in self._region:
            if cell in seen:
                continue
            components += 1
            seen |= self._reachable_from(cell)
        return components

    def solve(
        self,
        start: Optional[Coord] = None,
        goal: Optional[Coord] = None,
    ) -> List[Coord]:
        """Return a shortest path between two cells.

        Args:
            start: First cell, the maze entry by default.
            goal: Last cell, the maze exit by default.

        Returns:
            The list of cells from ``start`` to ``goal``, empty when they
            are not connected.
        """
        source = self.entry if start is None else start
        target = self.exit if goal is None else goal
        if not self.grid:
            return []
        previous: Dict[Coord, Coord] = {}
        seen: Set[Coord] = {source}
        queue: deque[Coord] = deque([source])
        while queue:
            current = queue.popleft()
            if current == target:
                break
            for neighbour in self.open_neighbours(*current):
                if neighbour in seen:
                    continue
                seen.add(neighbour)
                previous[neighbour] = current
                queue.append(neighbour)
        if target not in seen:
            return []
        path: List[Coord] = [target]
        while path[-1] != source:
            path.append(previous[path[-1]])
        path.reverse()
        return path

    @staticmethod
    def path_to_directions(path: Sequence[Coord]) -> str:
        """Convert a list of cells into ``N`` / ``E`` / ``S`` / ``W``.

        Args:
            path: Cells visited in order.

        Returns:
            One letter per move; an empty string for a path of one cell.

        Raises:
            MazeError: If two consecutive cells are not adjacent.
        """
        letters: List[str] = []
        for (from_x, from_y), (to_x, to_y) in zip(path, path[1:]):
            step = (to_x - from_x, to_y - from_y)
            for direction, delta in _DELTA.items():
                if delta == step:
                    letters.append(_LETTER[direction])
                    break
            else:
                raise MazeError(
                    f"cells {from_x},{from_y} and {to_x},{to_y} "
                    "are not adjacent"
                )
        return "".join(letters)

    def to_hex_lines(self) -> List[str]:
        """Return the maze as one hexadecimal digit per cell, row by row."""
        return ["".join(f"{cell:x}" for cell in row) for row in self.grid]

    # ------------------------------------------------------------------
    # Self validation
    # ------------------------------------------------------------------
    def check(self) -> List[str]:
        """Validate the generated maze against the project requirements.

        Returns:
            A list of human readable problems; empty when the maze is
            valid.
        """
        problems: List[str] = []
        problems.extend(self._check_borders())
        problems.extend(self._check_coherence())
        problems.extend(self._check_pattern())
        problems.extend(self._check_areas())
        if self._component_count() != 1:
            problems.append(
                "the corridors are not fully connected: "
                "some cells are isolated"
            )
        elif self.perfect:
            if self.loop_count() != 0:
                problems.append("a perfect maze must not contain any loop")
        else:
            problems.extend(self._check_playable())
        return problems

    def _check_borders(self) -> List[str]:
        """Check that the outer walls of the maze are all closed."""
        problems: List[str] = []
        for x in range(self.width):
            if not self.grid[0][x] & NORTH:
                problems.append(f"cell {x},0 opens through the north border")
            if not self.grid[self.height - 1][x] & SOUTH:
                problems.append(
                    f"cell {x},{self.height - 1} opens through "
                    "the south border"
                )
        for y in range(self.height):
            if not self.grid[y][0] & WEST:
                problems.append(f"cell 0,{y} opens through the west border")
            if not self.grid[y][self.width - 1] & EAST:
                problems.append(
                    f"cell {self.width - 1},{y} opens through "
                    "the east border"
                )
        return problems

    def _check_coherence(self) -> List[str]:
        """Check that neighbours agree on the wall they share."""
        problems: List[str] = []
        for y in range(self.height):
            for x in range(self.width):
                for direction in (EAST, SOUTH):
                    other_x, other_y = self._step(x, y, direction)
                    if not self._in_bounds(other_x, other_y):
                        continue
                    mine = bool(self.grid[y][x] & direction)
                    theirs = bool(
                        self.grid[other_y][other_x] & _OPPOSITE[direction]
                    )
                    if mine != theirs:
                        problems.append(
                            f"cells {x},{y} and {other_x},{other_y} "
                            "disagree on their shared wall"
                        )
        return problems

    def _check_pattern(self) -> List[str]:
        """Check that the pattern cells stay fully closed."""
        return [
            f"pattern cell {x},{y} is not fully closed"
            for x, y in sorted(self.pattern_cells)
            if self.grid[y][x] != ALL_WALLS
        ]

    def _check_areas(self) -> List[str]:
        """Check that no 3x3 area is completely open."""
        problems: List[str] = []
        for y in range(self.height - 2):
            for x in range(self.width - 2):
                if self.is_block_open(x, y, 3, 3):
                    problems.append(
                        f"the 3x3 area at {x},{y} is completely open"
                    )
        return problems

    def _check_playable(self) -> List[str]:
        """Check the extra rules of the Pac-Man (non perfect) board."""
        problems: List[str] = []
        if self.loop_count() < 2:
            problems.append(
                "a playable board needs at least two independent routes"
            )
        landmarks = {
            "north-west corner": (0, 0),
            "north-east corner": (self.width - 1, 0),
            "south-west corner": (0, self.height - 1),
            "south-east corner": (self.width - 1, self.height - 1),
            "centre": (self.width // 2, self.height // 2),
        }
        for name, (x, y) in landmarks.items():
            if (x, y) in self.pattern_cells or self.degree(x, y) == 0:
                problems.append(f"the {name} is not an open corridor")
        ends = self.dead_ends()
        if len(ends) > 2:
            listed = ", ".join(f"{x},{y}" for x, y in ends[:5])
            problems.append(
                f"a playable board should not keep {len(ends)} "
                f"dead-ends ({listed}...)"
            )
        return problems
