"""``KEY=VALUE`` 形式の設定ファイルの解析と検証。"""

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
    """設定ファイルを使えないときに送出する。"""


@dataclass(frozen=True)
class MazeConfig:
    """検証済みの設定ファイルの内容。

    Attributes:
        width: 迷路の列数。
        height: 迷路の行数。
        entry: 入口の ``(x, y)`` 座標。
        exit: 出口の ``(x, y)`` 座標。
        output_file: 生成した迷路を書き出すファイルのパス。
        perfect: 完全迷路なら ``True``、ゲーム盤なら ``False``。
        seed: 生成を再現可能にするシード。指定がなければ ``None``。
        algorithm: 使用する全域木アルゴリズムの名前。
        pattern: "42" のパターンを描くかどうか。
        color: 端末描画で ANSI カラーを使ってよいかどうか。
        display: ASCII 描画なら ``"terminal"``、MiniLibX ウィンドウなら
            ``"mlx"``。
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
    """``raw`` を整数に変換する。負の値も許す。"""
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"{key}: {raw!r} is not an integer") from None


def _parse_positive_int(key: str, raw: str) -> int:
    """``raw`` を正の整数に変換する。0 以下は認めない。"""
    value = _parse_integer(key, raw)
    if value <= 0:
        raise ConfigError(f"{key}: {value} must be strictly positive")
    return value


def _parse_bool(key: str, raw: str) -> bool:
    """``raw`` を真偽値に変換する。"""
    lowered = raw.strip().lower()
    if lowered in _TRUE_WORDS:
        return True
    if lowered in _FALSE_WORDS:
        return False
    raise ConfigError(
        f"{key}: {raw!r} is not a boolean (use True or False)"
    )


def _parse_coord(key: str, raw: str) -> Coord:
    """``raw`` を ``(x, y)`` の座標の組に変換する。"""
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
    """``raw`` が既知の生成アルゴリズム名かどうかを確かめる。"""
    lowered = raw.strip().lower()
    if lowered not in ALGORITHMS:
        known = ", ".join(ALGORITHMS)
        raise ConfigError(f"{key}: {raw!r} is unknown (try: {known})")
    return lowered


def _parse_display(key: str, raw: str) -> str:
    """``raw`` が既知の表示モード名かどうかを確かめる。"""
    lowered = raw.strip().lower()
    if lowered not in _DISPLAY_ALIASES:
        known = ", ".join(DISPLAYS)
        raise ConfigError(f"{key}: {raw!r} is unknown (try: {known})")
    return _DISPLAY_ALIASES[lowered]


def _parse_path(key: str, raw: str) -> str:
    """``raw`` が使えるファイル名かどうかを確かめる。"""
    if not raw:
        raise ConfigError(f"{key}: the file name must not be empty")
    return raw


def read_pairs(path: str) -> Dict[str, str]:
    """設定ファイルから ``KEY=VALUE`` の組を未加工のまま読み取る。

    Args:
        path: 設定ファイルのパス。

    Returns:
        大文字化したキーから、未加工の文字列値への対応表。

    Raises:
        ConfigError: ファイルが存在しない、読めない、または書式が不正な
            場合。
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
    """設定ファイルを読み込んで検証する。

    Args:
        path: 設定ファイルのパス。

    Returns:
        検証済みの設定。

    Raises:
        ConfigError: ファイルが存在しない、書式が不正、または内容に矛盾
            がある場合。
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
    """設定の意味的な整合性を確かめる。

    Args:
        config: 確認する設定。

    Raises:
        ConfigError: 設定が表す迷路が存在しえない場合。
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
