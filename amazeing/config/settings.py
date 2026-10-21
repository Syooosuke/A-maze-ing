"""設定ファイルを読み込み、値の形式を確かめた MazeConfig を作る。

読み取りは reader.py、値の変換は values.py が受け持つ。ここでは両者を
組み合わせるだけ。迷路として作れるか（大きさ、入口と出口の位置）は
MazeGenerator が確かめ、作れなければ MazeError を送出する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from amazeing.config.reader import MANDATORY_KEYS, ConfigError, read_pairs
from amazeing.config.values import (
    parse_bool,
    parse_coord,
    parse_int,
    parse_path,
    parse_positive_int,
)


@dataclass(frozen=True)
class MazeConfig:
    """値の形式を確かめ済みの設定。迷路として作れるかは MazeGenerator が確かめる。

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
    """設定ファイルを読み込み、各値を変換する。

    Raises:
        ConfigError: ファイルが読めない、書式が正しくない、必須キーが
            足りない、または値を変換できない場合。
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
    return MazeConfig(
        width=parse_positive_int("WIDTH", pairs["WIDTH"]),
        height=parse_positive_int("HEIGHT", pairs["HEIGHT"]),
        entry=parse_coord("ENTRY", pairs["ENTRY"]),
        exit=parse_coord("EXIT", pairs["EXIT"]),
        output_file=parse_path("OUTPUT_FILE", pairs["OUTPUT_FILE"]),
        perfect=parse_bool("PERFECT", pairs["PERFECT"]),
        seed=seed,
    )
