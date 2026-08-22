"""mazegen -- 依存関係のない小さな迷路生成モジュール。

長方形の迷路を作り、解いて、壁の対応関係が崩れないように保つ。公開する
クラスは MazeGenerator ひとつだけ。

使い方::

    from mazegen import MazeGenerator

    gen = MazeGenerator(width=21, height=15, seed=42)
    gen.generate()

    print(gen.grid[0])       # 1 行目の壁ビットマスク
    print(gen.solution)      # [(0, 0), (1, 0), ...]
    print(gen.directions)    # 'ESSEEN...'

主なコンストラクタ引数: width/height（格子の大きさ、2 以上）、
entry/exit（入口と出口の座標。exit の既定値は右下）、perfect（True
なら経路が 1 本の完全迷路、False ならループのある編み込み盤）、seed
（再現用のシード）、algorithm（backtracker/prim/kruskal）、pattern
（"42" のパターンを描くかどうか）。

generate() を呼んだ後は、grid（各セルの壁ビットマスク。NORTH=1,
EAST=2, SOUTH=4, WEST=8）、solution（入口から出口への最短経路）、
directions（同じ経路を N/E/S/W で表した文字列）、pattern_cells（描いた
パターンのセル集合）、seed_used（実際に使ったシード）から結果を読める。

ライセンス: MIT -- LICENSE.md を参照。
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
    """与えられた引数では迷路を作れないときに送出する。"""


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
    """text を scale 倍で描いたピクセル座標の集合と、その全体サイズを返す。"""
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
    """長方形の迷路を作り、編み込み、解く。

    壁はセルごとのビットマスクとして持つので、迷路の実体は
    List[List[int]] にすぎない。壁は必ず両側のセルへ同時に書き込むため、
    構造は作り方の時点で整合している。
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
        """引数を検証し、空の迷路を用意する。"""
        if width < 2 or height < 2:
            raise MazeError("maze size must be at least 2x2 cells")
        if width > 1000 or height > 1000:
            raise MazeError("maze size must not exceed 1000x1000 cells")
        if algorithm not in ALGORITHMS:
            known = ", ".join(ALGORITHMS)
            raise MazeError(f"unknown algorithm {algorithm!r} (known: {known})")
        for char in pattern_text:
            if char not in _GLYPHS:
                raise MazeError(f"no glyph available for {char!r}")

        self.width = width
        self.height = height
        self.entry = entry
        self.exit = (width - 1, height - 1) if exit is None else exit
        self.perfect = perfect
        self.seed = seed
        self.algorithm = algorithm
        self.pattern = pattern
        self.pattern_text = pattern_text

        self._check_endpoint(self.entry, "ENTRY")
        self._check_endpoint(self.exit, "EXIT")
        if self.entry == self.exit:
            raise MazeError("entry and exit must be different cells")

        self.grid: List[List[int]] = []
        self.pattern_cells: Set[Coord] = set()
        self.pattern_warning: Optional[str] = None
        self.solution: List[Coord] = []
        self.directions = ""
        self.seed_used = 0
        self._region: List[Coord] = []
        self._rng = random.Random(seed)

    # -- generation --

    def generate(self, seed: Optional[int] = None) -> "MazeGenerator":
        """迷路をまるごと作り直し、self を返す。

        seed を渡すとコンストラクタに渡したシードを上書きする。どちらも
        None のときはランダムなシードを引き、seed_used に記録する。
        """
        base = seed if seed is not None else self.seed
        if base is None:
            base = random.randrange(2 ** 32)
        self.seed_used = base
        self._rng = random.Random(base)

        self.grid = [[ALL_WALLS] * self.width for _ in range(self.height)]
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
        """cell が格子の外なら MazeError を送出する。"""
        x, y = cell
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise MazeError(
                f"{label} {x},{y} is outside the "
                f"{self.width}x{self.height} maze"
            )

    # -- "42" パターン --

    def _place_pattern(self) -> Tuple[Set[Coord], Optional[str]]:
        """パターンが収まる位置を探す。収まらなければ空集合と理由を返す。"""
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
        """shape を、外周から 1 マス空けて予約セルを避けつつ置ける場所を探す。

        置いた後も残りのセルがすべてつながっている必要がある。置き場所
        が見つからなければ None を返す。
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
        """blocked 以外のセルが連結のままかどうかを返す。"""
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

    # -- 全域木アルゴリズム --

    def _carve_spanning_tree(self) -> None:
        """パターン以外のすべてのセルに全域木を掘る。"""
        if self.algorithm == "prim":
            self._carve_prim()
        elif self.algorithm == "kruskal":
            self._carve_kruskal()
        else:
            self._carve_backtracker()

    def _carve_backtracker(self) -> None:
        """ランダム化した深さ優先探索（再帰的バックトラッカー）。"""
        start = self._rng.choice(self._region)
        visited: Set[Coord] = {start}
        stack: List[Coord] = [start]
        while stack:
            x, y = stack[-1]
            options: List[Tuple[int, Coord]] = []
            for direction in _DIRECTIONS:
                cell = self._step(x, y, direction)
                if cell not in visited and self._is_corridor(*cell):
                    options.append((direction, cell))
            if not options:
                stack.pop()
                continue
            direction, cell = self._rng.choice(options)
            self._carve(x, y, direction)
            visited.add(cell)
            stack.append(cell)

    def _carve_prim(self) -> None:
        """ランダム化した Prim のアルゴリズム。"""
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
        """cell の壁のうち、未訪問の通路に面するものを記録する。"""
        x, y = cell
        for direction in _DIRECTIONS:
            neighbour = self._step(x, y, direction)
            if self._is_corridor(*neighbour) and neighbour not in visited:
                frontier.append((cell, direction))

    def _corridor_edges(self) -> Iterator[Tuple[Coord, int]]:
        """通路セルが共有する壁を、1 枚につき 1 回ずつ返す。

        東と南の壁だけを見ることで、2 つのセルの間の壁を北側/西側の
        セルからのみ報告し、重複を避けている。
        """
        for x, y in self._region:
            for direction in (EAST, SOUTH):
                if self._is_corridor(*self._step(x, y, direction)):
                    yield (x, y), direction

    def _carve_kruskal(self) -> None:
        """Union-Find を使う、ランダム化した Kruskal のアルゴリズム。"""
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

    # -- 編み込み (Pac-Man モード) --

    def _braid(self) -> None:
        """行き止まりがなくなるまで壁を開ける。

        3x3 の完全な開放区画ができてしまう場合は開けないので、通路の幅
        が 2 セルを超えることはない。
        """
        while True:
            ends = [cell for cell in self._region if self.degree(*cell) <= 1]
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
                options.sort(key=lambda d: self.degree(*self._step(x, y, d)))
                self._carve(x, y, options[0])
                progress = True
            if not progress:
                return

    def _openable_walls(self, x: int, y: int) -> List[int]:
        """(x, y) の壁のうち、安全に開けられるものを列挙する。"""
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
        """迷路のループが target 個になるまで壁を開けていく。"""
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

    # -- 壁を扱う下位レベルのヘルパー --

    def _in_bounds(self, x: int, y: int) -> bool:
        """(x, y) が格子に含まれるかどうかを返す。"""
        return 0 <= x < self.width and 0 <= y < self.height

    def _is_corridor(self, x: int, y: int) -> bool:
        """(x, y) が迷路を掘り進めてよいセルかどうかを返す。"""
        return self._in_bounds(x, y) and (x, y) not in self.pattern_cells

    @staticmethod
    def _step(x: int, y: int, direction: int) -> Coord:
        """(x, y) の direction 側の隣のセルを返す。"""
        delta_x, delta_y = _DELTA[direction]
        return x + delta_x, y + delta_y

    def _carve(self, x: int, y: int, direction: int) -> None:
        """(x, y) と隣のセルの間の壁を開ける。"""
        other_x, other_y = self._step(x, y, direction)
        self.grid[y][x] &= ~direction
        self.grid[other_y][other_x] &= ~_OPPOSITE[direction]

    def _close(self, x: int, y: int, direction: int) -> None:
        """(x, y) と隣のセルの間の壁を閉じる。"""
        other_x, other_y = self._step(x, y, direction)
        self.grid[y][x] |= direction
        self.grid[other_y][other_x] |= _OPPOSITE[direction]

    def _creates_open_block(self, x: int, y: int, direction: int) -> bool:
        """壁を開けると 3x3 の開放区画ができるかどうかを返す。"""
        other_x, other_y = self._step(x, y, direction)
        self._carve(x, y, direction)
        found = self._open_block_around(x, y, other_x, other_y)
        self._close(x, y, direction)
        return found

    def _open_block_around(
        self, x: int, y: int, other_x: int, other_y: int
    ) -> bool:
        """与えられた 2 つのセルを含む 3x3 の開放区画を探す。"""
        low_x, high_x = min(x, other_x), max(x, other_x)
        low_y, high_y = min(y, other_y), max(y, other_y)
        xs = range(max(0, high_x - 2), min(low_x, self.width - 3) + 1)
        ys = range(max(0, high_y - 2), min(low_y, self.height - 3) + 1)
        for block_y in ys:
            for block_x in xs:
                if self.is_block_open(block_x, block_y, 3, 3):
                    return True
        return False

    def is_block_open(self, x: int, y: int, width: int, height: int) -> bool:
        """(x, y) を左上とする width x height の区画に、内側の壁が 1 枚も残っていないかを返す。"""
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

    # -- 公開の検査用ヘルパー --

    def walls_at(self, x: int, y: int) -> int:
        """セル (x, y) の閉じた壁のビットマスクを返す。"""
        return self.grid[y][x]

    def is_open(self, x: int, y: int, direction: int) -> bool:
        """(x, y) の direction 側の壁が開いているかを返す。"""
        return not self.grid[y][x] & direction

    def open_neighbours(self, x: int, y: int) -> Iterator[Coord]:
        """(x, y) から 1 歩で行けるセルを順に返す。"""
        for direction in _DIRECTIONS:
            if self.grid[y][x] & direction:
                continue
            neighbour = self._step(x, y, direction)
            if self._in_bounds(*neighbour):
                yield neighbour

    def degree(self, x: int, y: int) -> int:
        """(x, y) の壁のうち、開いているものの数を返す。"""
        return sum(1 for direction in _DIRECTIONS if not self.grid[y][x] & direction)

    def dead_ends(self) -> List[Coord]:
        """開いた壁が 1 枚しかない通路セルを返す。"""
        return [cell for cell in self._region if self.degree(*cell) == 1]

    def loop_count(self) -> int:
        """独立したループの数（循環的複雑度）を返す。"""
        edges = 0
        for x, y in self._region:
            for direction in (EAST, SOUTH):
                if not self.grid[y][x] & direction:
                    edges += 1
        return edges - len(self._region) + self._component_count()

    def _reachable_from(self, start: Coord) -> Set[Coord]:
        """開いた壁をたどって start とつながるセルをすべて返す。"""
        seen: Set[Coord] = {start}
        queue: deque[Coord] = deque([start])
        while queue:
            for neighbour in self.open_neighbours(*queue.popleft()):
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return seen

    def _component_count(self) -> int:
        """通路セルの連結成分の数を数える。"""
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
        """start から goal までの最短経路を返す（省略時は入口→出口、つながっていなければ空リスト）。"""
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
        """隣接するセルの並びを N/E/S/W の文字列に変換する。"""
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
        """迷路を 1 セル 16 進数 1 桁の形で、行ごとに返す。"""
        return ["".join(f"{cell:x}" for cell in row) for row in self.grid]

    # -- 自己検証 --

    def check(self) -> List[str]:
        """生成した迷路が要件を満たしているか検証し、問題点のリストを返す（正しければ空）。"""
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
        """迷路の外周の壁がすべて閉じているかを確かめる。"""
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
        """隣り合うセルが共有する壁について一致しているか確かめる。"""
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
        """パターンのセルが完全に閉じたままかを確かめる。"""
        return [
            f"pattern cell {x},{y} is not fully closed"
            for x, y in sorted(self.pattern_cells)
            if self.grid[y][x] != ALL_WALLS
        ]

    def _check_areas(self) -> List[str]:
        """3x3 の区画が完全に開いていないかを確かめる。"""
        problems: List[str] = []
        for y in range(self.height - 2):
            for x in range(self.width - 2):
                if self.is_block_open(x, y, 3, 3):
                    problems.append(
                        f"the 3x3 area at {x},{y} is completely open"
                    )
        return problems

    def _check_playable(self) -> List[str]:
        """Pac-Man 盤（非完全迷路）に固有の規則を確かめる。"""
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
