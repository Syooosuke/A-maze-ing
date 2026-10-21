"""設定ファイルを読み込み、検証済みの MazeConfig を作る。

読み取りは reader.py、値の変換は values.py が受け持つ。
ここでは両者を組み合わせ、値どうしの矛盾がないかを確かめる。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from amazeing.config.reader import MANDATORY_KEYS, ConfigError, read_pairs
from amazeing.config.values import (
    parse_bool,
    parse_coord,
    parse_int,
    parse_path,
    parse_positive_int,
)
from mazegen import MAX_SIZE, MIN_SIZE

__all__ = ["ConfigError", "MazeConfig", "load_config"]


@dataclass(frozen=True)
class MazeConfig:
    """検証済みの設定。

    Attributes:
        width, height: 迷路の列数と行数。
        entry, exit: 入口と出口の (x, y) 座標。
        output_file: 迷路を書き出すファイルのパス。
        perfect: 完全迷路なら True、Pac-Man 盤なら False。
        seed: 再現用のシード。指定がなければ None（毎回ランダム）。
    """

    width: int
    height: int
    entry: Tuple[int, int]
    exit: Tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int] = None


def load_config(path: str) -> MazeConfig:
    """設定ファイルを読み込んで検証する。

    Raises:
        ConfigError: ファイルが読めない、書式が正しくない、必須キーが
            足りない、または値どうしが矛盾している場合。
    """
    pairs = read_pairs(path)
    missing = [key for key in MANDATORY_KEYS if key not in pairs]
    if missing:
        raise ConfigError(
            f"{path}: missing mandatory key(s): {', '.join(missing)}"
        )

    seed = None
    if "SEED" in pairs:
        seed = parse_int("SEED", pairs["SEED"])
    config = MazeConfig(
        width=parse_positive_int("WIDTH", pairs["WIDTH"]),
        height=parse_positive_int("HEIGHT", pairs["HEIGHT"]),
        entry=parse_coord("ENTRY", pairs["ENTRY"]),
        exit=parse_coord("EXIT", pairs["EXIT"]),
        output_file=parse_path("OUTPUT_FILE", pairs["OUTPUT_FILE"]),
        perfect=parse_bool("PERFECT", pairs["PERFECT"]),
        seed=seed,
    )
    _check_consistency(config)
    return config


def _check_consistency(config: MazeConfig) -> None:
    """値どうしの矛盾を確かめる。見つかった問題はまとめて 1 回で報告する。"""
    problems: List[str] = []
    if config.width < MIN_SIZE or config.height < MIN_SIZE:
        problems.append(
            f"the maze must be at least {MIN_SIZE}x{MIN_SIZE} cells"
        )
    if config.width > MAX_SIZE or config.height > MAX_SIZE:
        problems.append(
            f"the maze must not exceed {MAX_SIZE}x{MAX_SIZE} cells"
        )
    for label, (x, y) in (("ENTRY", config.entry), ("EXIT", config.exit)):
        if x >= config.width or y >= config.height:
            problems.append(
                f"{label} {x},{y} is outside the "
                f"{config.width}x{config.height} maze"
            )
    if config.entry == config.exit:
        problems.append("ENTRY and EXIT must be different cells")
    if problems:
        raise ConfigError("; ".join(problems))
