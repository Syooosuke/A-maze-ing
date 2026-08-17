"""Interactive terminal front-end of the maze generator."""

from __future__ import annotations

import random
import sys
from typing import List, Optional

from amazeing.config import MazeConfig
from amazeing.output import OutputError, write_maze
from amazeing.render import THEMES, Theme, legend, render
from mazegen import MazeError, MazeGenerator

_MENU = (
    "1. Re-generate a new maze",
    "2. Show / Hide the shortest path",
    "3. Rotate the wall colours",
    '4. Toggle the "42" colours',
    "5. Save the maze to the output file",
    "6. Quit",
)


class Session:
    """Hold the maze and the display options of an interactive run."""

    def __init__(
        self, generator: MazeGenerator, config: MazeConfig
    ) -> None:
        """Prepare a session around an already generated maze.

        Args:
            generator: A generator on which ``generate()`` has been
                called.
            config: The configuration the maze was built from.
        """
        self.generator = generator
        self.config = config
        self.theme_index = 0
        self.show_path = False
        self.pattern_colour = True
        self.colour = config.color

    @property
    def theme(self) -> Theme:
        """Return the theme currently used to draw the maze."""
        return THEMES[self.theme_index]

    def regenerate(self) -> None:
        """Build a new maze with a fresh random seed.

        Raises:
            MazeError: If the new maze cannot be built.
        """
        self.generator.generate(seed=random.randrange(2 ** 32))

    def status(self) -> str:
        """Return a one line summary of the current maze."""
        generator = self.generator
        mode = "perfect" if generator.perfect else "playable board"
        return (
            f"{generator.width}x{generator.height} - {mode} - "
            f"{generator.algorithm} - seed {generator.seed_used} - "
            f"path {len(generator.solution)} cells - "
            f"{generator.loop_count()} loop(s) - "
            f"{len(generator.dead_ends())} dead-end(s)"
        )

    def screen(self) -> str:
        """Return the whole screen: maze, legend and status line."""
        picture = render(
            self.generator,
            theme=self.theme,
            show_path=self.show_path,
            colour=self.colour,
            pattern_colour=self.pattern_colour,
        )
        return "\n".join(
            (
                picture,
                "",
                legend(self.theme, self.colour, self.pattern_colour),
                self.status(),
            )
        )


def report_problems(generator: MazeGenerator) -> None:
    """Print on stderr the requirements the maze does not meet."""
    problems: List[str] = generator.check()
    for problem in problems:
        print(f"Warning: {problem}", file=sys.stderr)


def show(session: Session) -> None:
    """Print the maze and the informations around it."""
    print(session.screen())


def _prompt() -> Optional[str]:
    """Print the menu and read one choice, or ``None`` on end of input."""
    print()
    print("=== A-Maze-ing ===")
    for entry in _MENU:
        print(entry)
    try:
        return input(f"Choice? (1-{len(_MENU)}): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def run(session: Session) -> None:
    """Run the interactive menu until the user quits.

    Args:
        session: The session holding the maze and the display options.
    """
    show(session)
    while True:
        choice = _prompt()
        if choice is None or choice in ("6", "q", "quit"):
            print("Bye!")
            return
        if choice == "1":
            try:
                session.regenerate()
            except MazeError as error:
                print(f"Error: {error}", file=sys.stderr)
                continue
            report_problems(session.generator)
        elif choice == "2":
            session.show_path = not session.show_path
        elif choice == "3":
            session.theme_index = (session.theme_index + 1) % len(THEMES)
        elif choice == "4":
            session.pattern_colour = not session.pattern_colour
        elif choice == "5":
            _save(session)
            continue
        else:
            print(f"Unknown choice {choice!r}, please pick 1 to 6.")
            continue
        show(session)


def _save(session: Session) -> None:
    """Write the current maze to the configured output file."""
    path = session.config.output_file
    try:
        write_maze(path, session.generator)
    except OutputError as error:
        print(f"Error: {error}", file=sys.stderr)
        return
    print(f"Maze written to {path}")
