*This project has been created as part of the 42 curriculum by syokota, atajima.*

**English** | [日本語](README.ja.md)

# A-Maze-ing

## Description

**A-Maze-ing** generates mazes from a plain text configuration file, writes
them to disk using a compact hexadecimal wall encoding, and displays them in
the terminal with colours and an interactive menu.

Two very different kinds of maze can be produced from the same grid:

* `PERFECT=True` — a **perfect maze**: exactly one path between the entry
  and the exit, no loop anywhere. This is the classic lab maze.
* `PERFECT=False` (the value in `config.txt`) — a **playable Pac-Man
  board**: every corridor reachable, the four corners and the centre
  open, at least two independent loops, and dead-ends removed, so a chased
  player always has an alternative.

In both modes a **“42”** is drawn inside the maze with fully closed
cells, and the shortest path from the entry to the exit is computed and
exported.

The generation logic itself lives in a single standalone package,
[`mazegen/`](mazegen/), packaged as `mazegen-1.0.0-py3-none-any.whl` so
that a later project (a Pac-Man like game, for instance) can simply
`pip install` it.

## Instructions

Requirements: **Python 3.10 or later**. The program itself has **no runtime
dependency** — only the development tools (flake8, mypy, pytest, build) need
to be installed.

```bash
# Install the development tools in a local virtual environment (.venv)
make install

# Generate, save and display a maze using config.txt
make run
# ... which is exactly:
python3 a_maze_ing.py config.txt

# Use another configuration file
python3 a_maze_ing.py my_config.txt
make run CONFIG=my_config.txt

# Run under the Python debugger
make debug

# flake8 + mypy with the flags required by the subject
make lint
make lint-strict     # flake8 + mypy --strict

# Unit tests (the test suite is developed locally and, as the subject
# says, is not part of the submission)
make test

# Rebuild the pip package and refresh it at the root of the repository
make build

# Generate a maze and check it with the analysis script of the subject
# (copy maze_analyzer.py, provided with the subject, next to the Makefile)
make analyze

# Remove caches, build artefacts, then also the venv and maze.txt
make clean
make fclean

# List the rules of the Makefile
make help
```

### Interactive menu

The maze is displayed in the terminal. When both the standard input and
the standard output are terminals, the program then shows a menu
(otherwise it only prints the maze and exits):

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit
```

Colours are 256-colour ANSI codes. They are disabled automatically when the
output is redirected to a file or a pipe, or when the terminal's encoding
cannot display `██` — the rendering then falls back to plain ASCII (`##`
walls, `EE` entry, `XX` exit, `%%` for the “42”, `..` for the path).

## Configuration file

One `KEY=VALUE` pair per line. Lines starting with `#` and empty lines are
ignored, spaces around `=` are trimmed, and keys are case insensitive. An
unknown key, a duplicated key, a malformed line or an impossible maze all
produce a clear error message and exit status `1` — the program never
crashes on a bad input.

### Mandatory keys

| Key           | Description                                | Example                 |
| ------------- | ------------------------------------------ | ----------------------- |
| `WIDTH`       | Maze width, in cells (>= 2)                | `WIDTH=19`              |
| `HEIGHT`      | Maze height, in cells (>= 2)               | `HEIGHT=11`             |
| `ENTRY`       | Entry coordinates `x,y`                    | `ENTRY=0,0`             |
| `EXIT`        | Exit coordinates `x,y`, different from entry | `EXIT=18,10`          |
| `OUTPUT_FILE` | File receiving the generated maze          | `OUTPUT_FILE=maze.txt`  |
| `PERFECT`     | `True` for a perfect maze, `False` for a playable board | `PERFECT=False` |

### Optional keys

| Key         | Default        | Description                                     |
| ----------- | -------------- | ----------------------------------------------- |
| `SEED`      | random         | Integer seed; the same seed always rebuilds the same maze |

`PERFECT` accepts `True` or `False` (case insensitive). The maze is at most
1000×1000 cells, and a `PERFECT=False` board cannot be 2×2: such a grid can
hold only one loop, while a playable board needs two.

The default file is [`config.txt`](config.txt):

```ini
WIDTH=19
HEIGHT=11
ENTRY=0,0
EXIT=18,10
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
```

## Output file format

One hexadecimal digit per cell, one line per row. Each digit is the bitmask
of the **closed** walls of that cell:

| Bit       | Value | Direction |
| --------- | ----- | --------- |
| 0 (LSB)   | 1     | North     |
| 1         | 2     | East      |
| 2         | 4     | South     |
| 3         | 8     | West      |

So `3` (`0011`) means north and east are closed, south and west are open;
`A` (`1010`) means east and west are closed; `F` means the cell is fully
closed — that is how the “42” pattern is stored.

After the rows come an empty line and three more lines: the entry
coordinates, the exit coordinates, and the shortest path written with the
letters `N`, `E`, `S`, `W`. Every line ends with `\n`.

```
9139395539113915553
AC46C439406C46A9552
...
C546C5556C6C5545556

0,0
18,10
EESENESENEEESENEEESENESSEEESSESSSSWSES
```

Neighbouring cells always agree on the wall they share: walls are only ever
modified through `Grid.open_wall()` / `Grid.close_wall()`, which write both
sides at once, so incoherent data is impossible by construction.

## Maze generation algorithm

### Which one

The maze is carved with the **randomised depth-first search**, better known
as the **recursive backtracker**, implemented iteratively with an explicit
stack (so a 1000×1000 maze cannot blow the Python recursion limit). It
builds a *spanning tree* of the corridor cells, which is exactly the
definition of a perfect maze.

The generation runs in four stages:

1. **Place the “42”.** The digits are drawn from a 4×7 bitmap font (9×7
   cells in all), never touching the border, never covering the entry, the
   exit, a corner or the centre. The chosen placement must leave every
   remaining cell connected. Those cells stay at `F`, fully closed, and the
   maze is simply carved *around* them. A one-cell corridor is always kept
   between the “42” and the outer wall, so that the pattern never merges
   with the border and stays readable: the maze therefore needs at least
   11×9 cells to hold it. If it is smaller, or if the entry and the exit
   leave no room for it, the pattern is skipped and an error message is
   printed on the console.
2. **Carve a spanning tree** over every cell outside the pattern with the
   recursive backtracker. At this point the maze is perfect; when
   `PERFECT=True`, stage 3 is skipped. A tree has no loop, so it cannot
   contain a fully open 3×3 (or even 2×2) area.
3. **Braid** (only when `PERFECT=False`): while a cell has a single open
   wall, open one more of its walls, then open extra walls until there are
   at least two loops. A wall is only opened if it does not create a 3×3
   fully open area, so corridors never get wider than two cells. This keeps
   dead-ends rare, as the subject requires.
4. **Solve** the maze with a breadth-first search, which yields a genuinely
   *shortest* path.

### Why this one

* The recursive backtracker produces **long, winding corridors** with few
  junctions, which makes for a maze that is pleasant to look at and
  genuinely hard to solve — Prim and Kruskal tend to produce shorter,
  bushier branches. It is also the easiest of the classic algorithms to
  reason about, which matters when you have to explain your code during a
  defence.
* It is **O(number of cells)** in both time and memory, and works on any
  graph, so restricting it to “every cell except the 42 pattern” costs
  nothing: the pattern cells are simply never valid neighbours.
* Building a spanning tree first, then braiding, gives **both required
  modes from a single code path**, with the perfect maze as the exact
  intermediate state of the playable one.

The trade-off is that a raw backtracker maze is *very* dead-end heavy, which
is precisely why the braiding stage matters so much in Pac-Man mode.

### Correctness

`MazeGenerator.check()` re-validates a generated maze against every
requirement of the subject — closed borders, coherent shared walls, full
connectivity, fully closed pattern cells, no 3×3 open area, no loop when
perfect, and loops plus open corners, open centre and rare dead-ends when
playable. The program runs it after every generation and prints any problem
as a warning. The test suite additionally re-reads the **output file** and
re-checks everything from scratch, without using the generator internals.

### Checking with the analysis script of the subject

`maze_analyzer.py`, provided with the subject, is the reference oracle: it
re-reads an output file and reports the wall coherence and whether the maze
is *perfect* or a *playable* board. It is not committed here (it comes with
the subject, not from us); drop it next to the `Makefile` to use it.

```bash
make analyze
# or directly:
python3 maze_analyzer.py maze.txt
```

Both modes get the verdict the subject asks for:

```
# PERFECT=False
Verdict: Pac-Man-USABLE: fully connected, corners and centre reachable,
         21 independent routes; ...

# PERFECT=True
Verdict: PERFECT maze: a single path, no loop -> matches PERFECT=True ...
```

The analyzer calls our loops "independent routes": both count the same
thing.

The analyzer is also wired into our local test suite: mazes of different
sizes and seeds are generated and required to reach those verdicts. That
suite is not committed — the subject states the test programs are "not submitted or
graded" — but `make test` runs it whenever a `tests/` directory is present.

## What is reusable, and how

Everything needed to generate mazes lives in **one standalone package**,
[`mazegen/`](mazegen/), which has **no dependency** outside the standard
library and knows nothing about configuration files, terminals or colours.
It is published as a pip package at the root of this repository:

* `mazegen-1.0.0-py3-none-any.whl`

Everything needed to rebuild it is in the repository
([`pyproject.toml`](pyproject.toml)); `make build` regenerates the wheel.

```bash
python3 -m venv venv && source venv/bin/activate
pip install mazegen-1.0.0-py3-none-any.whl
# or, from the sources:
pip install build && python -m build
```

The rest of the code — [`a_maze_ing.py`](a_maze_ing.py) and the
[`amazeing/`](amazeing/) package (configuration, output file, rendering,
menu) — is the application layer and is *not* part of the package.

### Instantiate and use the generator

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=25, height=17, seed=42)
gen.generate()
```

### Pass custom parameters

```python
gen = MazeGenerator(
    width=31,            # columns, >= 2
    height=21,           # rows, >= 2
    entry=(0, 0),        # (x, y), must be inside the maze
    exit=(30, 20),       # (x, y), must differ from entry
    perfect=False,       # False -> braided, playable board
    seed=1234,           # None -> random, but always recorded
)
gen.generate()
```

Any invalid value (a size out of range, an entry or exit outside the maze,
entry equal to exit, a 2×2 playable board) raises `mazegen.MazeError` with
an explicit message, and so does a wrongly typed value (such as `"20"` or
`[0, 0]`). `perfect` defaults to `False`, like the `PERFECT` flag of the
subject ("If the PERFECT flag is not activated (the default)...").

### Access the generated structure and the solution

```python
from mazegen import EAST, NORTH, SOUTH, WEST

gen.grid              # List[List[int]], grid[y][x] = closed-wall bitmask
gen.grid[4][3] & EAST # non-zero when cell (3, 4) has its east wall closed

gen.pattern_cells     # Set[(x, y)] -- the fully closed "42" cells
gen.pattern_warning   # why the "42" was skipped, or None
gen.seed_used         # replay this seed to rebuild the very same maze

gen.solution          # [(0, 0), (1, 0), ...] shortest entry -> exit path
gen.directions        # the same path as "EEESSEES..." letters

gen.to_hex_lines()    # ['915155...', ...] one hex digit per cell
gen.dead_ends()       # cells with a single open wall
gen.loop_count()      # number of independent loops
gen.check()           # [] when the maze meets every requirement
```

A minimal integration in a game board:

```python
gen = MazeGenerator(19, 15, perfect=False, seed=7).generate()
board = [
    ["wall" if (x, y) in gen.pattern_cells else "corridor"
     for x in range(gen.width)]
    for y in range(gen.height)
]
```

A short version of this documentation is also the module docstring (in
Japanese, like the other docstrings), so `pydoc mazegen` or `help(mazegen)`
works after installing the package.

## Resources

Classic references used while working on this project:

* Jamis Buck, *Maze Generation Algorithms* series —
  <https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap>
  (the reference walkthrough of the backtracker, Prim and Kruskal).
* Jamis Buck, *Mazes for Programmers*, Pragmatic Bookshelf, 2015 — the
  chapter on **braiding** is where the dead-end removal idea comes from.
* Walter D. Pullen, *Think Labyrinth: Maze Algorithms* —
  <https://www.astrolog.org/labyrnth/algrithm.htm> (vocabulary: perfect,
  braided, unicursal mazes).
* Wikipedia, *Maze generation algorithm* and *Spanning tree* —
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>
* Python documentation: [`random`](https://docs.python.org/3/library/random.html),
  [`typing`](https://docs.python.org/3/library/typing.html),
  [PEP 257](https://peps.python.org/pep-0257/) (docstrings),
  [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
* [Choose a License](https://choosealicense.com/) — used to pick MIT for the
  reusable module.
* ANSI escape codes for the 256-colour terminal rendering —
  <https://en.wikipedia.org/wiki/ANSI_escape_code#256-colour_mode>

### How AI was used

AI (Claude) was used as a pair-programming assistant, on the following
tasks:

* **Exploring the algorithms** — asking for a comparison of the recursive
  backtracker, Prim and Kruskal before choosing one, then checking the
  claim that "a spanning tree over the corridor cells is exactly a perfect
  maze".
* **Bootstrapping the boilerplate** — the `KEY=VALUE` parser, the argument
  and error handling, the `Makefile` and the `pyproject.toml` were drafted
  with AI help and then reviewed line by line.
* **Debugging the “42” pattern** — the first bitmap font (3×5) created
  one-cell-wide pockets inside the digits that the braiding could not open,
  which left three unavoidable dead-ends. The diagnosis came out of a
  discussion with the AI; the fix (a 4×7 font whose holes are at least two
  cells thick) was implemented and verified with a randomised stress test
  over hundreds of maze sizes.
* **Reviewing the docstrings and this README**.

AI was **not** used as a black box: every generated snippet was read,
rewritten to match the rest of the code, and covered by a test. The
validation logic (`check()`, and the independent output-file parser in the
tests) was written specifically so that no AI-suggested shortcut could pass
unnoticed.

## Project structure

```
.
├── a_maze_ing.py                     # main program (entry point)
├── mazegen/                          # reusable package: MazeGenerator
│   ├── __init__.py                   # public API and module docstring
│   ├── generator.py                  # MazeGenerator: the generation steps
│   ├── validation.py                 # checks of the constructor arguments
│   ├── grid.py                       # Grid: cells and their walls
│   ├── constants.py                  # wall bits, directions, size range
│   ├── errors.py                     # MazeError
│   ├── generation/                   # building the maze
│   │   ├── pattern.py                # where the "42" goes
│   │   ├── glyphs.py                 # bitmap font of the "42"
│   │   ├── backtracker.py            # recursive backtracker
│   │   └── braiding.py               # dead-end removal, extra loops
│   └── analysis/                     # inspecting the result
│       ├── routes.py                 # shortest path, loops, dead-ends
│       └── verify.py                 # self-check against the subject
├── mazegen-1.0.0-py3-none-any.whl    # built pip package
├── amazeing/                         # the application (not packaged)
│   ├── output.py                     # output file writing
│   ├── config/                       # configuration file
│   │   ├── settings.py               # load_config(): builds a MazeConfig
│   │   ├── reader.py                 # reads the KEY=VALUE lines
│   │   └── values.py                 # converts the values (int, bool, x,y)
│   └── display/                      # terminal display
│       ├── canvas.py                 # what to draw where (no colours)
│       ├── themes.py                 # colour themes
│       ├── render.py                 # canvas -> terminal text
│       ├── session.py                # displayed maze and display options
│       ├── menu.py                   # interactive terminal menu
│       └── terminal.py               # is it a terminal, colour reset, ...
├── config.txt                        # default configuration
├── pyproject.toml                    # package build configuration
├── Makefile
├── .flake8                           # flake8 excludes (.venv, build, ...)
├── .gitignore                        # caches, venv, build, generated mazes
├── LICENSE.md                        # MIT, and why
├── README.md                         # this file (English)
└── README.ja.md                      # Japanese translation
```

Only the files required by the subject are committed, plus `.gitignore`,
`.flake8` and the Japanese README: no cache, no build leftover. `.flake8` tells flake8 to skip
the virtual environment created by `make install`, so that the plain
`flake8 .` asked by the subject checks our sources only. The test programs are
deliberately absent ("not submitted or graded"), and so is
`maze_analyzer.py`, which comes *with* the subject rather than from us.
Copy it next to the `Makefile` to use `make analyze`.

## Team and project management

### Roles

| Member     | Role                                                        |
| ---------- | ----------------------------------------------------------- |
| `atajima` | *generation algorithms and the reusable module*       |
| `syokota` | *configuration parsing, output file, error handling*  |

### Anticipated planning, and how it evolved

| Step | Planned                                   | What actually happened |
| ---- | ----------------------------------------- | ---------------------- |
| 1    | Config parsing and error handling         | Done first, as planned. The range checks (size, entry/exit) were later moved into `MazeGenerator` (`mazegen/validation.py`), so that the module stays safe when used without the config file and the rules live in one place. |
| 2    | Perfect maze generation + output file     | Started with the recursive backtracker only. Prim and Kruskal were added afterwards as a bonus, once `check()` could verify every algorithm automatically. |
| 3    | “42” pattern                              | Took longer than planned: the first 3×5 font left one-cell pockets that the braiding could not open. Replaced by a 4×7 font, placed so that the rest of the maze stays connected. |
| 4    | Braiding for the Pac-Man mode             | Done after the perfect maze, as planned. Braiding removes dead-ends and only opens a wall when no 3×3 open area appears; a final pass guarantees at least two loops. The subject's `maze_analyzer.py` was wired into the tests to confirm it. |
| 5    | Terminal rendering and menu               | The terminal renderer and its menu were done as planned. A MiniLibX window was added as an option, sharing the same canvas and colour themes; as the subject's wheels are Linux-only, it fell back to the terminal when `mlx` was unavailable (removed in step 6). |
| 6    | Packaging, README, licence                | The wheel, the MIT licence and the README came last, as planned. After that, the code was cleaned up for readability, a Japanese README was added, and `mazegen.py` was split into a layered package without changing its public API. Finally, the bonuses (Prim, Kruskal) and the optional features (MiniLibX window, save menu, extra configuration keys) were removed, to keep the submission small and quick to review; unused public methods and re-exports were dropped afterwards. |

### What worked well, what could be improved

* **Worked well:** keeping `mazegen` completely independent from the
  application layer from day one — it made the package trivial to build,
  and the module easy to test in isolation.
* **Worked well:** writing `check()` early. Every requirement of the subject
  became an assertion, and the randomised stress test caught the pattern
  dead-end bug that a single hand-picked maze would have hidden.
* **Worked well:** wiring the subject's `maze_analyzer.py` into the tests.
  It is the exact oracle the project is graded against, so there was no
  guessing left about the Pac-Man rules.
* **To improve:** the braiding is greedy and could be smarter about where it
  opens walls, which would give more regular, more Pac-Man looking boards.

### Tools

* **Git** for versioning.
* **`make`** to standardise install / run / debug / lint / test / build.
* **flake8** (PEP 8) and **mypy** (`--strict` — the whole project passes)
  for static checking.
* **pytest** for the unit tests, including a randomised stress test.
* **`build` + setuptools** for the pip package.
* **`maze_analyzer.py`** (provided with the subject) as the reference
  validator, both from `make analyze` and from the test suite.
* **Claude** as a pair-programming assistant, see *Resources* above.
