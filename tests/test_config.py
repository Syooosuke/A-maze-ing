"""Unit tests of the configuration file parser."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

import a_maze_ing
from amazeing.config import ConfigError, load_config

_VALID = """
# A comment
WIDTH=20
HEIGHT=15

ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
"""


def write(tmp_path: Path, text: str) -> str:
    """Write ``text`` into a temporary config file and return its path."""
    path = tmp_path / "config.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_valid_configuration(tmp_path: Path) -> None:
    """Comments and empty lines are ignored, values are converted."""
    config = load_config(write(tmp_path, _VALID))
    assert config.width == 20
    assert config.height == 15
    assert config.entry == (0, 0)
    assert config.exit == (19, 14)
    assert config.output_file == "maze.txt"
    assert config.perfect is True
    assert config.seed is None


def test_optional_keys(tmp_path: Path) -> None:
    """The optional SEED key is read as an integer."""
    config = load_config(write(tmp_path, _VALID + "SEED=7\n"))
    assert config.seed == 7


def test_spaces_and_case_are_tolerated(tmp_path: Path) -> None:
    """``  width = 20 `` is the same as ``WIDTH=20``."""
    text = _VALID.replace("WIDTH=20", "  width = 20  ")
    config = load_config(write(tmp_path, text))
    assert config.width == 20


def test_missing_file() -> None:
    """A missing file is reported, not raised as an OSError."""
    with pytest.raises(ConfigError, match="not found"):
        load_config("does-not-exist.txt")


@pytest.mark.parametrize(
    "text, message",
    [
        (_VALID.replace("WIDTH=20\n", ""), "missing mandatory"),
        (_VALID.replace("WIDTH=20", "WIDTH=abc"), "not an integer"),
        (_VALID.replace("WIDTH=20", "WIDTH=0"), "strictly positive"),
        (_VALID.replace("ENTRY=0,0", "ENTRY=0"), "coordinates"),
        (_VALID.replace("ENTRY=0,0", "ENTRY=0,x"), "non-integer"),
        (_VALID.replace("PERFECT=True", "PERFECT=maybe"), "boolean"),
        (_VALID + "SEED=x\n", "not an integer"),
        (_VALID + "ALGORITHM=prim\n", "unknown key"),
        (_VALID.replace("PERFECT=True", "PERFECT=yes"), "boolean"),
        (_VALID + "WIDTH=30\n", "defined twice"),
        (_VALID + "COLOUR=True\n", "unknown key"),
        (_VALID + "this is not a pair\n", "KEY=VALUE"),
        (_VALID.replace("OUTPUT_FILE=maze.txt", "OUTPUT_FILE="), "empty"),
    ],
)
def test_invalid_configurations(
    tmp_path: Path, text: str, message: str
) -> None:
    """Every malformed configuration gets a specific error message."""
    with pytest.raises(ConfigError, match=message):
        load_config(write(tmp_path, text))


def test_a_directory_is_not_a_config_file(tmp_path: Path) -> None:
    """Pointing at a directory is reported gracefully."""
    with pytest.raises(ConfigError):
        load_config(str(tmp_path))


@pytest.mark.parametrize(
    "text, message",
    [
        (_VALID.replace("WIDTH=20", "WIDTH=1"), "at least 2x2"),
        (_VALID.replace("WIDTH=20", "WIDTH=5000"), "must not exceed"),
        (_VALID.replace("ENTRY=0,0", "ENTRY=99,0"), "outside"),
        (_VALID.replace("EXIT=19,14", "EXIT=0,0"), "different cells"),
    ],
)
def test_impossible_mazes_are_reported(
    tmp_path: Path, text: str, message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The generator rejects an impossible maze; the program reports it."""
    assert a_maze_ing.main(["a_maze_ing.py", write(tmp_path, text)]) == 1
    error = capsys.readouterr().err
    assert error.startswith("Error: ")
    assert message in error


def test_playable_2x2_is_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A 2x2 grid cannot hold the two loops of a playable board."""
    text = _VALID.replace("WIDTH=20", "WIDTH=2")
    text = text.replace("HEIGHT=15", "HEIGHT=2")
    text = text.replace("EXIT=19,14", "EXIT=1,1").replace(
        "PERFECT=True", "PERFECT=False"
    )
    assert a_maze_ing.main(["a_maze_ing.py", write(tmp_path, text)]) == 1
    assert "too small for a playable board" in capsys.readouterr().err


def test_invalid_output_file_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A NUL byte in OUTPUT_FILE is an error, not a traceback."""
    text = _VALID.replace("OUTPUT_FILE=maze.txt", "OUTPUT_FILE=a\x00b")
    assert a_maze_ing.main(["a_maze_ing.py", write(tmp_path, text)]) == 1
    assert "not a valid file name" in capsys.readouterr().err


def test_closed_standard_streams(tmp_path: Path) -> None:
    """Closed stdin/stdout must not crash the program."""
    import subprocess
    import sys

    output = tmp_path / "maze.txt"
    config = write(tmp_path, _VALID.replace(
        "OUTPUT_FILE=maze.txt", f"OUTPUT_FILE={output}"
    ))
    for kwargs in ({"stdin": None}, {"stdout": None}):
        result = subprocess.run(
            [sys.executable, "a_maze_ing.py", config],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, text=True,
            pass_fds=(), close_fds=True,
            preexec_fn=_closer(0 if "stdin" in kwargs else 1),
        )
        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stderr


def _closer(fd: int) -> Callable[[], None]:
    """Return a function that closes ``fd`` in the child process."""
    import os

    return lambda: os.close(fd)
