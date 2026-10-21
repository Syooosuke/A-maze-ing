"""設定ファイルの値（文字列）を、整数・真偽値・座標などに変換する。

どの関数も、変換できなければキーの名前を含んだ ConfigError を送出する。
"""

from __future__ import annotations

from typing import Tuple

from amazeing.config.reader import ConfigError


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
    """True / False を真偽値に変換する。大文字と小文字は区別しない。"""
    word = raw.strip().lower()
    if word == "true":
        return True
    if word == "false":
        return False
    raise ConfigError(f"{key}: {raw!r} is not a boolean (use True or False)")


def parse_coord(key: str, raw: str) -> Tuple[int, int]:
    """「x,y」 を座標 (x, y) に変換する。負の座標は認めない。"""
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


def parse_path(key: str, raw: str) -> str:
    """ファイル名が空でないことを確かめる。"""
    if not raw:
        raise ConfigError(f"{key}: the file name must not be empty")
    return raw
