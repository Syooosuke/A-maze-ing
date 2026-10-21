"""設定ファイルの値（文字列）を、整数・真偽値・座標などに変換する。

どの関数も、変換できなければキーの名前を含んだ ConfigError を送出する。
"""

from __future__ import annotations

from typing import Tuple

from amazeing.config_reader import ConfigError
from mazegen import ALGORITHMS

TRUE_WORDS = ("true", "yes", "on", "1")
FALSE_WORDS = ("false", "no", "off", "0")

DISPLAYS: Tuple[str, ...] = ("terminal", "mlx")
# DISPLAY に書いてよい言葉と、それが表す表示モード。
DISPLAY_ALIASES = {
    "terminal": "terminal",
    "ascii": "terminal",
    "text": "terminal",
    "mlx": "mlx",
    "minilibx": "mlx",
    "graphic": "mlx",
}


def parse_int(key: str, raw: str) -> int:
    """整数に変換する。負の値も許す。"""
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"{key}: {raw!r} is not an integer") from None


def parse_positive_int(key: str, raw: str) -> int:
    """1 以上の整数に変換する。"""
    value = parse_int(key, raw)
    if value <= 0:
        raise ConfigError(f"{key}: {value} must be strictly positive")
    return value


def parse_bool(key: str, raw: str) -> bool:
    """True/False（yes/no, on/off, 1/0 も可）を真偽値に変換する。"""
    word = raw.strip().lower()
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ConfigError(f"{key}: {raw!r} is not a boolean (use True or False)")


def parse_coord(key: str, raw: str) -> Tuple[int, int]:
    """"x,y" を座標 (x, y) に変換する。負の座標は認めない。"""
    parts = raw.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key}: {raw!r} is not a 'x,y' pair of coordinates")
    try:
        x, y = int(parts[0]), int(parts[1])
    except ValueError:
        raise ConfigError(
            f"{key}: {raw!r} contains non-integer coordinates"
        ) from None
    if x < 0 or y < 0:
        raise ConfigError(f"{key}: {raw!r} must not be negative")
    return x, y


def parse_algorithm(key: str, raw: str) -> str:
    """生成アルゴリズムの名前を確かめ、小文字にそろえて返す。"""
    name = raw.strip().lower()
    if name not in ALGORITHMS:
        known = ", ".join(ALGORITHMS)
        raise ConfigError(f"{key}: {raw!r} is unknown (try: {known})")
    return name


def parse_display(key: str, raw: str) -> str:
    """表示モードの名前を確かめ、"terminal" か "mlx" にそろえて返す。"""
    name = raw.strip().lower()
    if name not in DISPLAY_ALIASES:
        known = ", ".join(DISPLAYS)
        raise ConfigError(f"{key}: {raw!r} is unknown (try: {known})")
    return DISPLAY_ALIASES[name]


def parse_path(key: str, raw: str) -> str:
    """ファイル名が空でないことを確かめる。"""
    if not raw:
        raise ConfigError(f"{key}: the file name must not be empty")
    return raw
