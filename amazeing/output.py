"""Writing of the maze output file."""

from __future__ import annotations

from typing import List

from mazegen import MazeGenerator


class OutputError(Exception):
    """Raised when the maze cannot be written to disk."""


def build_lines(generator: MazeGenerator) -> List[str]:
    """Build the exact content of the output file, line by line.

    The layout is the one described by the subject: one hexadecimal digit
    per cell, one line per row, an empty line, then the entry, the exit
    and the shortest path.

    Args:
        generator: A generator on which ``generate()`` has been called.

    Returns:
        The lines of the file, without their trailing newline.
    """
    lines = generator.to_hex_lines()
    lines.append("")
    lines.append(f"{generator.entry[0]},{generator.entry[1]}")
    lines.append(f"{generator.exit[0]},{generator.exit[1]}")
    lines.append(generator.directions)
    return lines


def write_maze(path: str, generator: MazeGenerator) -> None:
    """Write the maze to ``path``.

    Args:
        path: Destination file; it is overwritten when it exists.
        generator: A generator on which ``generate()`` has been called.

    Raises:
        OutputError: If the file cannot be written.
    """
    payload = "".join(f"{line}\n" for line in build_lines(generator))
    try:
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(payload)
    except IsADirectoryError:
        raise OutputError(f"{path!r} is a directory, not a file") from None
    except PermissionError:
        raise OutputError(f"no permission to write {path!r}") from None
    except FileNotFoundError:
        raise OutputError(
            f"the directory of {path!r} does not exist"
        ) from None
    except OSError as error:
        raise OutputError(f"cannot write {path!r}: {error}") from None
