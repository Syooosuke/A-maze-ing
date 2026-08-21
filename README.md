*This project has been created as part of the 42 curriculum by syokota, atajima.*

**English** | [日本語](README.ja.md)

> **TODO before submitting:** replace `<login1>` above (and add
> `, <login2>, <login3>` if you worked as a team) with your real 42
> login(s), and fill in the *Team and project management* section at the
> bottom with your own answers.

# A-Maze-ing

## Description

**A-Maze-ing** generates mazes from a plain text configuration file, writes
them to disk using a compact hexadecimal wall encoding, and displays them in
the terminal with colours and an interactive menu.

Two very different kinds of maze can be produced from the same grid:

* `PERFECT=True` — a **perfect maze**: exactly one path between the entry
  and the exit, no loop anywhere. This is the classic lab maze.
* `PERFECT=False` (the default) — a **playable Pac-Man board**: every
  corridor reachable, the four corners and the centre open, many
  independent routes, and **no dead-end at all**, so a chased player is
  never trapped.

In both modes a large **“42”** is drawn inside the maze with fully closed
cells, and the shortest path from the entry to the exit is computed and
exported.

The generation logic itself lives in a single standalone module,
[`mazegen.py`](mazegen.py), packaged as `mazegen-1.0.0-py3-none-any.whl` so
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

# Optional: install the MiniLibX wrapper for the graphical display (Linux)
# (copy mlx-2.2.tgz, provided with the subject, next to the Makefile)
make install-mlx

# Remove caches, build artefacts, then also the venv and maze.txt
make clean
make fclean
```

### Displays

Two renderings are available, selected with the `DISPLAY` key of the
configuration file:

* `DISPLAY=terminal` (default) — ANSI colour rendering in the terminal,
  with a numbered menu;
* `DISPLAY=mlx` — a **MiniLibX window**, driven with the keyboard.

The MiniLibX is *optional*: it is not a dependency of the project. If the
`mlx` package is missing, or if no display is available, the program prints
a warning and falls back to the terminal rendering — it never fails because
of it.

```bash
# with mlx-2.2.tgz (provided with the subject) at the root of the repository
make install-mlx     # unpacks it and installs the right wheel
# then set DISPLAY=mlx in config.txt
```

`mlx-2.2.tgz` ships Linux wheels only (`fedora/` and `ubuntu/`), so the
window works on the school clusters; on macOS the fallback takes over. The
archive is not committed here: it is provided with the subject, not by us.

In the window: `1` regenerate, `2` show/hide the path, `3` rotate the wall
colours, `4` toggle the “42” colours, `5` save, `6`/`Esc` quit. The whole
maze is drawn into one MiniLibX image and blitted in a single call, and the
colour themes are shared with the terminal renderer (the xterm‑256 palette
is converted to RGB).

### Interactive menu

With `DISPLAY=terminal`, when the standard input is a terminal, the program
shows a menu after displaying the maze:

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Toggle the "42" colours
5. Save the maze to the output file
6. Quit
```

Colours are 256-colour ANSI codes. They are disabled automatically when the
output is redirected, when the `NO_COLOR` environment variable is set, or
when `COLOR=False` appears in the configuration file — the rendering then
falls back to plain ASCII (`##` walls, `EE` entry, `XX` exit, `%%` for the
“42”, `..` for the path).

## Configuration file

One `KEY=VALUE` pair per line. Lines starting with `#` and empty lines are
ignored, spaces around `=` are trimmed, and keys are case insensitive. An
unknown key, a duplicated key, a malformed line or an impossible maze all
produce a clear error message and exit status `1` — the program never
crashes on a bad input.

### Mandatory keys

| Key           | Description                                | Example                 |
| ------------- | ------------------------------------------ | ----------------------- |
| `WIDTH`       | Maze width, in cells (>= 2)                | `WIDTH=25`              |
| `HEIGHT`      | Maze height, in cells (>= 2)               | `HEIGHT=17`             |
| `ENTRY`       | Entry coordinates `x,y`                    | `ENTRY=0,0`             |
| `EXIT`        | Exit coordinates `x,y`, different from entry | `EXIT=24,16`          |
| `OUTPUT_FILE` | File receiving the generated maze          | `OUTPUT_FILE=maze.txt`  |
| `PERFECT`     | `True` for a perfect maze, `False` for a playable board | `PERFECT=False` |

### Optional keys

| Key         | Default        | Description                                     |
| ----------- | -------------- | ----------------------------------------------- |
| `SEED`      | random         | Integer seed; the same seed always rebuilds the same maze |
| `ALGORITHM` | `backtracker`  | `backtracker`, `prim` or `kruskal`              |
| `PATTERN`   | `True`         | Draw the “42” pattern                           |
| `COLOR`     | `True`         | Allow ANSI colours in the terminal rendering    |
| `DISPLAY`   | `terminal`     | `terminal` or `mlx` (MiniLibX window)           |

Booleans accept `True`/`False`, `yes`/`no`, `on`/`off`, `1`/`0`.

The default file is [`config.txt`](config.txt):

```ini
WIDTH=25
HEIGHT=17
ENTRY=0,0
EXIT=24,16
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
ALGORITHM=backtracker
PATTERN=True
COLOR=True
DISPLAY=terminal
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
`a` (`1010`) means east and west are closed; `f` means the cell is fully
closed — that is how the “42” pattern is stored.

After the rows come an empty line and three more lines: the entry
coordinates, the exit coordinates, and the shortest path written with the
letters `N`, `E`, `S`, `W`. Every line ends with `\n`.

```
9155551395515555555555393
ac3ff96c2ff83ffffffff946a
...
c555455556c46c456c46c5556

0,0
24,16
EEEEEEESENEEESESSEESSSWWSWSESSSSSSSESENEEESENEESEEEE
```

Neighbouring cells always agree on the wall they share: walls are only ever
modified through a single private helper that writes both sides at once, so
incoherent data is impossible by construction.

## Maze generation algorithm

### Which one

The default algorithm is the **randomised depth-first search**, better known
as the **recursive backtracker**, implemented iteratively with an explicit
stack (so a 1000×1000 maze cannot blow the Python recursion limit).
**Randomised Prim** and **randomised Kruskal** are also available through
the `ALGORITHM` key — all three build a *spanning tree* of the corridor
cells, which is exactly the definition of a perfect maze.

The generation runs in four stages:

1. **Place the “42”.** The digits are drawn from a 4×7 bitmap font, scaled
   up as large as the grid allows (never more than 30 % of the cells, never
   touching the border, never covering the entry, the exit, a corner or the
   centre). The chosen placement must leave every remaining cell connected.
   Those cells stay at `f`, fully closed, and the maze is simply carved
   *around* them. If the maze is too small to hold the pattern, it is
   skipped and a message is printed on the console.
2. **Carve a spanning tree** over every cell outside the pattern with the
   selected algorithm. At this point the maze is perfect, and the work is
   over when `PERFECT=True`.
3. **Braid** (only when `PERFECT=False`): while a cell has a single open
   wall, open one more of its walls. A wall is only opened if it does not
   create a 3×3 fully open area, so corridors never get wider than two
   cells. This removes **every** dead-end, which is the bonus asked for by
   the subject.
4. **Guarantee at least two loops** and **solve** the maze with a
   breadth-first search, which yields a genuinely *shortest* path.

### Why this one

* The recursive backtracker produces **long, winding corridors** with few
  junctions, which makes for maze that is pleasant to look at and genuinely
  hard to solve — Prim and Kruskal tend to produce shorter, bushier
  branches. It is also the easiest of the three to reason about, which
  matters when you have to explain your code during a defence.
* It is **O(number of cells)** in both time and memory, and works on any
  graph, so restricting it to “every cell except the 42 pattern” costs
  nothing: the pattern cells are simply never valid neighbours.
* Building a spanning tree first, then braiding, gives **both required
  modes from a single code path**, with the perfect maze as the exact
  intermediate state of the playable one.

The trade-off is that a raw backtracker maze is *very* dead-end heavy, which
is precisely why the braiding stage matters so much in Pac-Man mode. Prim
and Kruskal were kept because they braid into slightly different looking
boards, and because comparing them is a good way to check that the
validation code does not depend on the algorithm.

### Correctness

`MazeGenerator.check()` re-validates a generated maze against every
requirement of the subject — closed borders, coherent shared walls, full
connectivity, fully closed pattern cells, no 3×3 open area, no loop when
perfect, and loops plus open corners, open centre and no dead-end when
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
# or directly, with the strictest threshold (the no-dead-end bonus):
python3 maze_analyzer.py maze.txt --max-dead-ends 0
```

Both modes reach the best possible verdict:

```
# PERFECT=False
Dead-ends        : 0 real + 0 enclosed by the '42' (tolerated)
Corners + centre : all reachable
Wall coherence   : OK (all shared walls match)
Verdict: Pac-Man-USABLE: fully connected, corners and centre reachable,
         33 independent routes; no real dead-end -> bonus-grade
         (perfectly braided).

# PERFECT=True
Verdict: PERFECT maze: a single path, no loop -> matches PERFECT=True
```

The analyzer is also wired into our local test suite: dozens of mazes, of
different sizes, seeds and algorithms, are generated and required to reach
those verdicts with `--min-loops 2 --max-dead-ends 0`. That suite is not
committed — the subject states the test programs are "not submitted or
graded" — but `make test` runs it whenever a `tests/` directory is present.

## What is reusable, and how

Everything needed to generate mazes lives in **one standalone module**,
[`mazegen.py`](mazegen.py), which has **no dependency** outside the standard
library and knows nothing about configuration files, terminals or colours.
It is published as a pip package at the root of this repository:

* `mazegen-1.0.0-py3-none-any.whl`

Everything needed to rebuild it is in the repository
([`pyproject.toml`](pyproject.toml)); `make build` regenerates both files.

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
    algorithm="prim",    # "backtracker", "prim" or "kruskal"
    pattern=True,        # draw the "42"
    pattern_text="42",   # what to draw
)
gen.generate()
```

Any invalid combination raises `mazegen.MazeError` with an explicit message.

### Access the generated structure and the solution

```python
from mazegen import EAST, NORTH, SOUTH, WEST

gen.grid              # List[List[int]], grid[y][x] = closed-wall bitmask
gen.walls_at(3, 4)    # the same value, read through a method
gen.is_open(3, 4, EAST)          # True when you can walk east
list(gen.open_neighbours(3, 4))  # the cells reachable in one step
gen.degree(3, 4)                 # how many walls are open

gen.pattern_cells     # Set[(x, y)] -- the fully closed "42" cells
gen.pattern_warning   # why the "42" was skipped, or None
gen.seed_used         # replay this seed to rebuild the very same maze

gen.solution          # [(0, 0), (1, 0), ...] shortest entry -> exit path
gen.directions        # the same path as "ESSEEN..." letters
gen.solve((3, 3), (7, 9))        # shortest path between any two cells

gen.to_hex_lines()    # ['9155...', ...] one hex digit per cell
gen.dead_ends()       # cells with a single open wall
gen.loop_count()      # number of independent routes
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

The full documentation is also the module docstring, so `pydoc mazegen` or
`help(mazegen)` works after installing the package. It holds both an English
and a Japanese version; the docstrings of the rest of the code are in
Japanese.

## Advanced features

* **Three generation algorithms** — recursive backtracker, randomised Prim,
  randomised Kruskal, selected with the `ALGORITHM` key.
* **Zero dead-end braided boards** — the bonus asked by the subject: in
  `PERFECT=False` mode the generator removes *every* dead-end while keeping
  corridors at most two cells wide.
* **Scalable “42” pattern** — the digits are drawn from a bitmap font and
  automatically scaled to the largest size the grid can host.
* **Two displays** — an ANSI terminal renderer and an optional **MiniLibX**
  window, sharing the same canvas and the same colour themes.
* **Five colour themes** rotated live from the menu, with a separate toggle
  for the “42” colours, and automatic fallback to plain ASCII.
* **Self-validation** — `check()` verifies every rule of the subject after
  each generation.
* **Reproducibility** — even a maze generated without a seed records the
  seed it used, so it can always be replayed.

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

<!-- TODO: adjust this section so that it describes what YOU actually did. -->

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
├── mazegen.py                        # reusable module: MazeGenerator
├── mazegen-1.0.0-py3-none-any.whl    # built pip package
├── amazeing/
│   ├── config.py                     # KEY=VALUE parsing and validation
│   ├── output.py                     # output file writing
│   ├── render.py                     # terminal rendering, colour themes
│   ├── ui.py                         # interactive menu
│   └── mlxview.py                    # optional MiniLibX window
├── config.txt                        # default configuration
├── pyproject.toml                    # package build configuration
├── Makefile
├── LICENSE.md                        # MIT, and why
├── README.md                         # this file (English)
└── README.ja.md                      # Japanese translation
```

Only the files required by the subject are committed: no tool
configuration file of our own, no cache, no build leftover. The
development tools and the flake8 excludes live in the `Makefile` itself, so
that nothing outside this list has to be tracked. The test programs are
deliberately absent ("not submitted or graded"), and so are the two files
that come *with* the subject rather than from us: `maze_analyzer.py` and
`mlx-2.2.tgz`. Copy them next to the `Makefile` to use `make analyze` and
`make install-mlx`.

## Team and project management

<!-- TODO: this section must describe YOUR team and YOUR planning. -->

### Roles

| Member     | Role                                                        |
| ---------- | ----------------------------------------------------------- |
| `<login1>` | *(e.g. generation algorithms and the reusable module)*       |
| `<login2>` | *(e.g. configuration parsing, output file, error handling)*  |
| `<login3>` | *(e.g. terminal rendering, interactive menu, packaging)*     |

### Anticipated planning, and how it evolved

| Step | Planned                                   | What actually happened |
| ---- | ----------------------------------------- | ---------------------- |
| 1    | Config parsing and error handling         | *(fill in)*            |
| 2    | Perfect maze generation + output file     | *(fill in)*            |
| 3    | “42” pattern                              | *(fill in)*            |
| 4    | Braiding for the Pac-Man mode             | *(fill in)*            |
| 5    | Terminal rendering and menu               | *(fill in)*            |
| 6    | Packaging, README, licence                | *(fill in)*            |

### What worked well, what could be improved

* **Worked well:** keeping `mazegen.py` completely independent from the
  application layer from day one — it made the package trivial to build,
  and the module easy to test in isolation.
* **Worked well:** writing `check()` early. Every requirement of the subject
  became an assertion, and the randomised stress test caught the pattern
  dead-end bug that a single hand-picked maze would have hidden.
* **To improve:** the braiding is greedy and could be smarter about where it
  opens walls, which would give more regular, more Pac-Man looking boards.
* **Worked well:** wiring the subject's `maze_analyzer.py` into the tests.
  It is the exact oracle the project is graded against, so there was no
  guessing left about the Pac-Man rules.
* **To improve:** the MiniLibX viewer is tested through an injected double
  rather than against a real window, because the wheels shipped with the
  subject are Linux-only — the rendering logic is covered, the actual X11
  window has to be checked by hand on a cluster machine.

### Tools

* **Git** for versioning.
* **`make`** to standardise install / run / debug / lint / test / build.
* **flake8** (PEP 8) and **mypy** (`--strict` — the whole project passes)
  for static checking.
* **pytest** for the unit tests, including a randomised stress test.
* **`build` + setuptools** for the pip package.
* **`maze_analyzer.py`** (provided with the subject) as the reference
  validator, both from `make analyze` and from the test suite.
* **MiniLibX** (`mlx-2.2.tgz`, provided with the subject) for the optional
  graphical display.
* **Claude** as a pair-programming assistant, see *Resources* above.
