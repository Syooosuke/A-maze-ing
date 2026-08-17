#!/usr/bin/env python3
"""A-Maze-ing -- generate a maze from a configuration file.

Usage::

    python3 a_maze_ing.py config.txt

The maze is written to the file named by ``OUTPUT_FILE`` and displayed in
the terminal.  When the standard input is a terminal, an interactive menu
lets the user regenerate the maze, toggle the shortest path and change the
colours.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

from amazeing.config import ConfigError, MazeConfig, load_config
from amazeing.mlxview import MlxUnavailable, show_in_window
from amazeing.output import OutputError, write_maze
from amazeing.ui import Session, report_problems, run, show
from mazegen import MazeError, MazeGenerator

USAGE = "Usage: python3 a_maze_ing.py <config file>"


def build_generator(config: MazeConfig) -> MazeGenerator:
    """Create the generator described by ``config``.

    Args:
        config: A validated configuration.

    Returns:
        A generator, ready to be used but not generated yet.

    Raises:
        MazeError: If the configuration describes an impossible maze.
    """
    return MazeGenerator(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.perfect,
        seed=config.seed,
        algorithm=config.algorithm,
        pattern=config.pattern,
    )


def use_colour(config: MazeConfig) -> bool:
    """Tell whether the terminal output may use ANSI colours."""
    if not config.color:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


def run_program(config_path: str) -> int:
    """Load a configuration, generate a maze and display it.

    Args:
        config_path: Path of the configuration file.

    Returns:
        The exit status of the program.
    """
    config = load_config(config_path)
    generator = build_generator(config)
    generator.generate()

    if generator.pattern_warning is not None:
        print(f"Warning: {generator.pattern_warning}", file=sys.stderr)
    report_problems(generator)

    write_maze(config.output_file, generator)
    print(f"Maze written to {config.output_file}")

    session = Session(generator, config)
    session.colour = use_colour(config)
    if config.display == "mlx" and show_window(session):
        return 0
    if sys.stdin.isatty():
        run(session)
    else:
        show(session)
    return 0


def show_window(session: Session) -> bool:
    """Try to display the maze in a MiniLibX window.

    Args:
        session: The session holding the maze and the display options.

    Returns:
        ``True`` when the window was shown, ``False`` when the caller must
        fall back to the terminal rendering.
    """
    try:
        show_in_window(session)
    except MlxUnavailable as error:
        print(f"Warning: {error}", file=sys.stderr)
        print(
            "Warning: falling back to the terminal rendering.",
            file=sys.stderr,
        )
        return False
    return True


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point of the program.

    Args:
        argv: Command line arguments, ``sys.argv`` by default.

    Returns:
        ``0`` on success, ``1`` on any handled error.
    """
    args = sys.argv if argv is None else argv
    if len(args) != 2:
        print(USAGE, file=sys.stderr)
        return 1
    if args[1] in ("-h", "--help"):
        print(USAGE)
        return 0
    try:
        return run_program(args[1])
    except (ConfigError, MazeError, OutputError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
