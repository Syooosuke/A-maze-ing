"""Parsing and validation of the ``KEY=VALUE`` configuration file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from mazegen import ALGORITHMS

Coord = Tuple[int, int]

MANDATORY_KEYS: Tuple[str, ...] = (
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
)
OPTIONAL_KEYS: Tuple[str, ...] = (
    "SEED",
    "ALGORITHM",
    "PATTERN",
    "COLOR",
    "DISPLAY",
)
KNOWN_KEYS: Tuple[str, ...] = MANDATORY_KEYS + OPTIONAL_KEYS

_TRUE_WORDS = frozenset({"true", "yes", "on", "1"})
_FALSE_WORDS = frozenset({"false", "no", "off", "0"})

DISPLAYS: Tuple[str, ...] = ("terminal", "mlx")
_DISPLAY_ALIASES = {
    "terminal": "terminal",
    "ascii": "terminal",
    "text": "terminal",
    "mlx": "mlx",
    "minilibx": "mlx",
    "graphic": "mlx",
}


class ConfigError(Exception):
    """Raised when the configuration file cannot be used."""


@dataclass(frozen=True)
class MazeConfig:
    """Validated content of a configuration file.

    Attributes:
        width: Number of columns of the maze.
        height: Number of rows of the maze.
        entry: ``(x, y)`` coordinates of the entrance.
        exit: ``(x, y)`` coordinates of the exit.
        output_file: Path of the file receiving the generated maze.
        perfect: ``True`` for a perfect maze, ``False`` for a game board.
        seed: Seed making the generation reproducible, or ``None``.
        algorithm: Name of the spanning tree algorithm to use.
        pattern: Whether the "42" pattern must be drawn.
        color: Whether the terminal rendering may use ANSI colours.
        display: ``"terminal"`` for the ASCII rendering, ``"mlx"`` for a
            MiniLibX window.
    """

    width: int
    height: int
    entry: Coord
    exit: Coord
    output_file: str
    perfect: bool
    seed: Optional[int] = None
    algorithm: str = "backtracker"
    pattern: bool = True
    color: bool = True
    display: str = "terminal"


def _parse_integer(key: str, raw: str) -> int:
    """Convert ``raw`` into any integer, negative values included."""
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"{key}: {raw!r} is not an integer") from None


def _parse_positive_int(key: str, raw: str) -> int:
    """Convert ``raw`` into a strictly positive integer."""
    value = _parse_integer(key, raw)
    if value <= 0:
        raise ConfigError(f"{key}: {value} must be strictly positive")
    return value


def _parse_bool(key: str, raw: str) -> bool:
    """Convert ``raw`` into a boolean."""
    lowered = raw.strip().lower()
    if lowered in _TRUE_WORDS:
        return True
    if lowered in _FALSE_WORDS:
        return False
    raise ConfigError(
        f"{key}: {raw!r} is not a boolean (use True or False)"
    )


def _parse_coord(key: str, raw: str) -> Coord:
    """Convert ``raw`` into a ``(x, y)`` pair of coordinates."""
    parts = raw.split(",")
    if len(parts) != 2:
        raise ConfigError(
            f"{key}: {raw!r} is not a 'x,y' pair of coordinates"
        )
    try:
        x, y = int(parts[0]), int(parts[1])
    except ValueError:
        raise ConfigError(
            f"{key}: {raw!r} contains non-integer coordinates"
        ) from None
    if x < 0 or y < 0:
        raise ConfigError(f"{key}: {raw!r} must not be negative")
    return x, y


def _parse_algorithm(key: str, raw: str) -> str:
    """Check that ``raw`` names a known generation algorithm."""
    lowered = raw.strip().lower()
    if lowered not in ALGORITHMS:
        known = ", ".join(ALGORITHMS)
        raise ConfigError(f"{key}: {raw!r} is unknown (try: {known})")
    return lowered


def _parse_display(key: str, raw: str) -> str:
    """Check that ``raw`` names a known display mode."""
    lowered = raw.strip().lower()
    if lowered not in _DISPLAY_ALIASES:
        known = ", ".join(DISPLAYS)
        raise ConfigError(f"{key}: {raw!r} is unknown (try: {known})")
    return _DISPLAY_ALIASES[lowered]


def _parse_path(key: str, raw: str) -> str:
    """Check that ``raw`` is a usable file name."""
    if not raw:
        raise ConfigError(f"{key}: the file name must not be empty")
    return raw


def read_pairs(path: str) -> Dict[str, str]:
    """Read the raw ``KEY=VALUE`` pairs of a configuration file.

    Args:
        path: Path of the configuration file.

    Returns:
        A mapping of upper-cased keys to their raw string value.

    Raises:
        ConfigError: If the file is missing, unreadable or malformed.
    """
    try:
        with open(path, "r", encoding="utf-8") as stream:
            lines = stream.readlines()
    except FileNotFoundError:
        raise ConfigError(f"configuration file {path!r} not found") from None
    except IsADirectoryError:
        raise ConfigError(f"{path!r} is a directory, not a file") from None
    except PermissionError:
        raise ConfigError(f"no permission to read {path!r}") from None
    except UnicodeDecodeError:
        raise ConfigError(f"{path!r} is not a readable text file") from None
    except OSError as error:
        raise ConfigError(f"cannot read {path!r}: {error}") from None

    pairs: Dict[str, str] = {}
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise ConfigError(
                f"{path}:{number}: {stripped!r} is not a KEY=VALUE line"
            )
        raw_key, raw_value = stripped.split("=", 1)
        key = raw_key.strip().upper()
        if not key:
            raise ConfigError(f"{path}:{number}: the key is missing")
        if key not in KNOWN_KEYS:
            known = ", ".join(KNOWN_KEYS)
            raise ConfigError(
                f"{path}:{number}: unknown key {key!r} (known: {known})"
            )
        if key in pairs:
            raise ConfigError(f"{path}:{number}: {key} is defined twice")
        pairs[key] = raw_value.strip()
    return pairs


def load_config(path: str) -> MazeConfig:
    """Read and validate a configuration file.

    Args:
        path: Path of the configuration file.

    Returns:
        The validated configuration.

    Raises:
        ConfigError: If the file is missing, malformed or inconsistent.
    """
    pairs = read_pairs(path)
    missing = [key for key in MANDATORY_KEYS if key not in pairs]
    if missing:
        raise ConfigError(
            f"{path}: missing mandatory key(s): {', '.join(missing)}"
        )

    raw_seed = pairs.get("SEED")
    config = MazeConfig(
        width=_parse_positive_int("WIDTH", pairs["WIDTH"]),
        height=_parse_positive_int("HEIGHT", pairs["HEIGHT"]),
        entry=_parse_coord("ENTRY", pairs["ENTRY"]),
        exit=_parse_coord("EXIT", pairs["EXIT"]),
        output_file=_parse_path("OUTPUT_FILE", pairs["OUTPUT_FILE"]),
        perfect=_parse_bool("PERFECT", pairs["PERFECT"]),
        seed=(
            None if raw_seed is None else _parse_integer("SEED", raw_seed)
        ),
        algorithm=_parse_algorithm(
            "ALGORITHM", pairs.get("ALGORITHM", "backtracker")
        ),
        pattern=_parse_bool("PATTERN", pairs.get("PATTERN", "True")),
        color=_parse_bool("COLOR", pairs.get("COLOR", "True")),
        display=_parse_display(
            "DISPLAY", pairs.get("DISPLAY", "terminal")
        ),
    )
    _validate(config)
    return config


def _validate(config: MazeConfig) -> None:
    """Check the semantic consistency of a configuration.

    Args:
        config: The configuration to check.

    Raises:
        ConfigError: If the described maze cannot exist.
    """
    problems: List[str] = []
    if config.width < 2 or config.height < 2:
        problems.append("the maze must be at least 2x2 cells")
    if config.width > 1000 or config.height > 1000:
        problems.append("the maze must not exceed 1000x1000 cells")
    for label, cell in (("ENTRY", config.entry), ("EXIT", config.exit)):
        x, y = cell
        if x >= config.width or y >= config.height:
            problems.append(
                f"{label} {x},{y} is outside the "
                f"{config.width}x{config.height} maze"
            )
    if config.entry == config.exit:
        problems.append("ENTRY and EXIT must be different cells")
    if problems:
        raise ConfigError("; ".join(problems))
