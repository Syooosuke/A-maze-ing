*This project has been created as part of the 42 curriculum by syokota, atajima.*

**English** | [日本語](README.ja.md)

# A-Maze-ing

## Description

This program reads a configuration file, builds a maze, writes it to a file
and shows it in the terminal.

The `PERFECT` key chooses between two kinds of maze:

* `PERFECT=True`: a perfect maze. There is only one path from the entry to
  the exit, and no loops.
* `PERFECT=False` (what `config.txt` uses): a board for a Pac-Man-like
  game. Every corridor can be reached, the four corners and the centre are
  corridors, there are at least two loops, and walls are opened so
  that no dead-ends are left.

In both modes a "42" made of fully closed cells is drawn inside the maze
(if the maze is at least 11×9),
and the shortest path from the entry to the exit is written to the output
file.

The maze generator itself is a separate package, `mazegen/`. It is shipped
as `mazegen-1.0.0-py3-none-any.whl`, so another project can
`pip install` it.

## Instructions

You need Python 3.10 or later. The program only uses the standard library.
`make install` only installs the development tools (flake8, mypy, build).

```bash
# install the development tools in .venv
make install

# build and show a maze from config.txt (same as python3 a_maze_ing.py config.txt)
make run

# use another configuration file
python3 a_maze_ing.py my_config.txt
make run CONFIG=my_config.txt

# run it under pdb
make debug

# flake8 and mypy with the options from the subject
make lint
make lint-strict     # flake8 and mypy --strict

# rebuild the wheel (after make install)
make build

# check the maze with the subject's maze_analyzer.py
# (put maze_analyzer.py next to the Makefile first)
make analyze

make clean     # remove caches and build files
make fclean    # clean, and also remove .venv and maze.txt
make help      # list the rules
```

### Menu

After the maze is shown, a menu appears if both the standard input and the
standard output are terminals (otherwise the program just prints the maze
and exits).

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit
```

Colours use 256-colour ANSI codes. When the output goes to a file or a pipe,
or when the terminal cannot show `██`, the maze is drawn with plain
characters instead (`##` walls, `EE` entry, `XX` exit, `%%` for the "42",
`..` for the path).

## Configuration file

One `KEY=VALUE` per line. Empty lines and lines starting with `#` are
ignored, spaces around `=` are removed and keys are not case sensitive. With
an unknown key, a key given twice, a missing key, a malformed line or a maze
that cannot be built, the program prints an error message and exits with
status 1.

### Mandatory keys

| Key           | Meaning                                    | Example                 |
| ------------- | ------------------------------------------ | ----------------------- |
| `WIDTH`       | width in cells (2 or more)                 | `WIDTH=19`              |
| `HEIGHT`      | height in cells (2 or more)                | `HEIGHT=11`             |
| `ENTRY`       | entry coordinates `x,y`                    | `ENTRY=0,0`             |
| `EXIT`        | exit coordinates `x,y`, not the entry      | `EXIT=18,10`            |
| `OUTPUT_FILE` | file the maze is written to                | `OUTPUT_FILE=maze.txt`  |
| `PERFECT`     | `True` for a perfect maze, `False` for a Pac-Man board | `PERFECT=False` |

### Optional keys

| Key    | If missing | Meaning                                         |
| ------ | ---------- | ----------------------------------------------- |
| `SEED` | random     | integer seed; the same seed gives the same maze |

`PERFECT` must be `True` or `False` (any case). A maze can be at most
1000×1000 cells. A 2×2 maze with `PERFECT=False` is refused, because a 2×2
grid can only have one loop.

This is `config.txt`:

```ini
WIDTH=19
HEIGHT=11
ENTRY=0,0
EXIT=18,10
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
```

## Output file

One hexadecimal digit per cell, one line per row of the maze. Each digit
tells which walls of the cell are closed:

| Bit     | Value | Direction |
| ------- | ----- | --------- |
| 0 (LSB) | 1     | North     |
| 1       | 2     | East      |
| 2       | 4     | South     |
| 3       | 8     | West      |

For example `3` (`0011`) means north and east are closed, and `A` (`1010`)
means east and west are closed. `F` is a fully closed cell. The "42" is made
of these.

After the rows there is an empty line, then the entry, the exit and the
shortest path written with `N`, `E`, `S` and `W`. Every line ends with `\n`.

```
9139395539113915553
AC46C439406C46A9552
...
C546C5556C6C5545556

0,0
18,10
EESENESENEEESENEEESENESSEEESSESSSSWSES
```

Walls are only changed through `Grid.open_wall()` and `Grid.close_wall()`,
which always update both neighbouring cells, so two cells can never disagree
about the wall between them.

## Maze generation algorithm

### Which one

The maze is carved with the recursive backtracker (a randomised depth-first
search). It uses an explicit stack instead of recursion, so even a
1000×1000 maze does not hit Python's recursion limit. The backtracker
builds a spanning tree of the corridor cells, and a spanning tree is a
perfect maze.

The maze is built in four steps:

1. Place the "42". Two 4×7 glyphs (9×7 cells in total) are placed so that
   they do not cover the entry, the exit, a corner or the centre, and so
   that the other cells stay connected. We always keep a one-cell corridor
   between the "42" and the outer wall, so the maze must be at least 11×9.
   If it is smaller, or if the entry and the exit leave no room, the "42" is
   skipped and an error message is printed.
2. Carve a spanning tree over every cell outside the "42" with the
   backtracker. A tree has no loop, so there is no open 3×3 area (not even
   2×2).
3. Braid (only with `PERFECT=False`). Each dead-end (a cell with one open
   wall) gets one more wall opened, again and again until no more can be
   opened. If there are still fewer than two loops, more walls are opened
   until there are two (in our tests this only happened on very small or
   thin mazes, such as 2×3 or 12×2). A wall is
   never opened if that would create an open 3×3 area, so corridors
   are at most two cells wide.
4. Solve. A breadth-first search finds the shortest path from the entry to
   the exit.

### Why this one

* The backtracker makes long, winding corridors, which looks like a real
  maze. We also looked at Prim and Kruskal, but they tend to give lots of
  short branches. The backtracker's code is also short and easy to follow.
* It runs in time proportional to the number of cells.
* We first build a tree and then braid it, so both modes use the same code.

### Checking the result

`MazeGenerator.check()` checks a generated maze against the subject: closed
outer walls, matching walls between neighbours, full connectivity, closed
"42" cells, no open 3×3 area, no loop for a perfect maze, and for a Pac-Man
board at least two loops, open corners and centre and at most two dead-ends.
The program runs it after every generation and prints a warning if
something is wrong.

### Checking with the subject's maze_analyzer.py

We also check the output with `maze_analyzer.py`, which comes with the
subject. It is not ours, so it is not in this repository. Put it next to the
`Makefile` to use it.

```bash
make analyze
# or
python3 maze_analyzer.py maze.txt
```

Both modes get the expected verdict:

```
# PERFECT=False
Verdict: Pac-Man-USABLE: fully connected, corners and centre reachable,
         21 independent routes; ...

# PERFECT=True
Verdict: PERFECT maze: a single path, no loop -> matches PERFECT=True ...
```

What the analyzer calls "independent routes" is what we call loops.

Our local tests (`tests/`) also run this script on mazes of several sizes
and seeds. The subject says tests are "not submitted or graded", so they are not
committed.

## What is reusable, and how

Everything that builds the maze is in the [`mazegen/`](mazegen/) package.
It only uses the standard library and knows nothing about configuration
files or the terminal. It is built as a wheel and committed at the root of
the repository:

* `mazegen-1.0.0-py3-none-any.whl`

[`pyproject.toml`](pyproject.toml) is in the repository too, so
`make build` can rebuild the wheel.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install mazegen-1.0.0-py3-none-any.whl

# or, instead of the line above, rebuild it from the sources
# (the wheel goes to dist/)
pip install build && python -m build --wheel
pip install dist/mazegen-1.0.0-py3-none-any.whl
```

[`a_maze_ing.py`](a_maze_ing.py) and [`amazeing/`](amazeing/)
(configuration, output file, display, menu) belong to this program only and
are not in the package.

Inside the package, `Grid` holds the cells and walls, and the functions in
`generation/` (building) and `analysis/` (checking) work on it.
`MazeGenerator.generate()` calls them in order, so it shows the whole
generation flow.

### Create a maze

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=25, height=17, seed=42)
gen.generate()
```

### Custom parameters

```python
gen = MazeGenerator(
    width=31,            # columns, 2 to 1000
    height=21,           # rows, 2 to 1000
    entry=(0, 0),        # (x, y), (0, 0) if omitted
    exit=(30, 20),       # (x, y), bottom-right corner if omitted
    perfect=False,       # False (the default) gives a Pac-Man board
    seed=1234,           # random if omitted, kept in gen.seed_used
)
gen.generate()
```

`generate()` returns the generator, so you can write
`MazeGenerator(...).generate()`. `generate(seed=...)` builds the maze again
with another seed.

A size out of range, an entry or exit outside the maze, the same cell for
entry and exit, a 2×2 Pac-Man board or a value of the wrong type (such as
`"20"` or `[0, 0]`) raises `mazegen.MazeError`.

### Read the result

```python
from mazegen import EAST

gen.grid              # grid[y][x] is the closed-wall bitmask (List[List[int]])
gen.grid[4][3] & EAST # non-zero if cell (3, 4) has its east wall closed

gen.pattern_cells     # the cells of the "42"
gen.pattern_warning   # why the "42" was skipped, or None
gen.seed_used         # the seed used, to build the same maze again

gen.solution          # shortest path from entry to exit [(0, 0), (1, 0), ...]
gen.directions        # the same path as letters "EEESSEES..."

gen.to_hex_lines()    # the hex rows ['915155...', ...]
gen.dead_ends()       # cells with only one open wall
gen.loop_count()      # number of loops
gen.check()           # [] if every requirement is met
```

For example, to turn it into a game board:

```python
gen = MazeGenerator(19, 15, perfect=False, seed=7).generate()
board = [
    ["wall" if (x, y) in gen.pattern_cells else "corridor"
     for x in range(gen.width)]
    for y in range(gen.height)
]
```

A shorter version of this is in the package docstring (`pydoc mazegen` or
`help(mazegen)`).

## Resources

* Jamis Buck, *Maze Generation Algorithms* (the backtracker, Prim and
  Kruskal explained)
  <https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap>
* Jamis Buck, *Mazes for Programmers*, Pragmatic Bookshelf, 2015 (the
  chapter on braiding gave us the idea for removing dead-ends)
* Walter D. Pullen, *Think Labyrinth: Maze Algorithms* (words like perfect
  and braided) <https://www.astrolog.org/labyrnth/algrithm.htm>
* Wikipedia: *Maze generation algorithm* and *Spanning tree*
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>,
  <https://en.wikipedia.org/wiki/Spanning_tree>
* Python documentation:
  [`random`](https://docs.python.org/3/library/random.html),
  [`typing`](https://docs.python.org/3/library/typing.html),
  [PEP 257](https://peps.python.org/pep-0257/),
  [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
* [Choose a License](https://choosealicense.com/) (we used it to pick MIT)
* ANSI escape codes (256 colours)
  <https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit>

### How we used AI

We used AI (Claude) for:

* comparing the backtracker, Prim and Kruskal before choosing an algorithm
* first drafts of the configuration reader (`amazeing/config/`), the error
  handling, the `Makefile` and `pyproject.toml`, which we then read and
  fixed
* finding why the first 3×5 glyphs left dead-ends inside the "42" (we
  switched to 4×7 glyphs, `mazegen/generation/glyphs.py`)
* splitting the code into files by role (`mazegen/`, `amazeing/`) and
  reviewing the code and this README

## Project structure

```
.
├── a_maze_ing.py                     # main program
├── mazegen/                          # reusable package
│   ├── __init__.py                   # public names and docstring
│   ├── generator.py                  # MazeGenerator (the generation steps)
│   ├── validation.py                 # argument checks
│   ├── grid.py                       # Grid (cells and walls)
│   ├── constants.py                  # wall bits, directions, size range, ...
│   ├── errors.py                     # MazeError
│   ├── generation/                   # building the maze
│   │   ├── pattern.py                # where the "42" goes
│   │   ├── glyphs.py                 # the "42" glyphs
│   │   ├── backtracker.py            # recursive backtracker
│   │   └── braiding.py               # removing dead-ends, adding loops
│   └── analysis/                     # looking at the result
│       ├── routes.py                 # shortest path, loops, dead-ends
│       └── verify.py                 # requirement checks
├── mazegen-1.0.0-py3-none-any.whl    # the package (wheel)
├── amazeing/                         # the rest of the program
│   ├── output.py                     # writes the output file
│   ├── config/                       # configuration file
│   │   ├── settings.py               # load_config()
│   │   ├── reader.py                 # reads the KEY=VALUE lines
│   │   └── values.py                 # converts the values
│   └── display/                      # terminal display
│       ├── canvas.py                 # what to draw where
│       ├── themes.py                 # colour themes
│       ├── render.py                 # turns the canvas into text
│       ├── session.py                # current maze and display options
│       ├── menu.py                   # the menu
│       └── terminal.py               # terminal checks, colour reset, ...
├── config.txt                        # example configuration
├── pyproject.toml                    # package build settings
├── Makefile
├── .flake8                           # keeps flake8 out of .venv
├── .gitignore
├── LICENSE.md                        # MIT licence
├── README.md                         # this file
└── README.ja.md                      # Japanese version
```

The tests and `maze_analyzer.py` (which comes with the subject) are not
committed. `.flake8` is there so that `flake8 .` does not go into the
`.venv` created by `make install`.

## Team and project management

### Roles

| Member    | Role                                                |
| --------- | --------------------------------------------------- |
| `atajima` | generation algorithms and the reusable module       |
| `syokota` | configuration parsing, output file, error handling  |

### Planning and how it went

| Step | Plan                                  | What happened |
| ---- | ------------------------------------- | ------------- |
| 1    | Config parsing and error handling     | Done first, as planned. The size and entry/exit checks were later moved into `MazeGenerator` (`mazegen/validation.py`). |
| 2    | Perfect maze and output file          | Done with the backtracker. |
| 3    | The "42"                              | Took longer than planned. The 3×5 glyphs left dead-ends, so we switched to 4×7. |
| 4    | Pac-Man board (braiding)              | Done after the perfect maze, as planned, with the 3×3 check and the "at least two loops" step. |
| 5    | Terminal display and menu             | Done as planned. |
| 6    | Package, README, licence              | Wheel, licence and README came after the display. Then we split the code into files by role and went over everything once more. |

### What worked, what could be better

What worked:

* Keeping `mazegen` separate from the display and the configuration from
  the start. Making the package and testing it on its own was easy.
* Writing `check()` early, so every maze we generated was tested against
  the subject's rules. Running it on random seeds is also how we found the
  dead-ends caused by the "42" glyphs.
* Using the subject's `maze_analyzer.py` in our tests, so we never had to
  guess the Pac-Man rules.

What could be better:

* Braiding just prefers the wall towards the neighbour with the fewest open
  walls and picks at random otherwise. With more work the boards could look
  more like a real Pac-Man level.

### Tools

* Git
* make (install, run, debug, lint, build)
* flake8 and mypy (`--strict` passes too)
* pytest
* build and setuptools for the wheel
* the subject's `maze_analyzer.py`
