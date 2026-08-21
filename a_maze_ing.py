#!/usr/bin/env python3
"""A-Maze-ing -- 設定ファイルから迷路を生成する。

使い方::

    python3 a_maze_ing.py config.txt

生成した迷路は ``OUTPUT_FILE`` が指すファイルに書き出し、端末にも表示
する。標準入力が端末のときは対話メニューを開き、迷路の再生成、最短経路
の表示切り替え、配色の変更ができる。
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
    """``config`` が表す生成器を作る。

    Args:
        config: 検証済みの設定。

    Returns:
        すぐ使える生成器。ただし生成はまだ実行していない。

    Raises:
        MazeError: 設定が生成不可能な迷路を表している場合。
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
    """端末出力で ANSI カラーを使ってよいかどうかを返す。"""
    return (
        config.color
        and os.environ.get("NO_COLOR") is None
        and sys.stdout.isatty()
    )


def run_program(config_path: str) -> int:
    """設定を読み込み、迷路を生成して表示する。

    Args:
        config_path: 設定ファイルのパス。

    Returns:
        プログラムの終了ステータス。
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
    """MiniLibX のウィンドウで迷路を表示してみる。

    Args:
        session: 迷路と表示オプションを保持するセッション。

    Returns:
        ウィンドウを表示できたら ``True``。呼び出し側が端末描画へ
        フォールバックすべきなら ``False``。
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
    """プログラムのエントリポイント。

    Args:
        argv: コマンドライン引数。既定では ``sys.argv``。

    Returns:
        成功なら ``0``、処理済みのエラーが起きたなら ``1``。
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
    except (ConfigError, MazeError, OutputError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
