#!/usr/bin/env python3
"""A-Maze-ing -- 設定ファイルから迷路を生成し、保存して表示する。

使い方::

    python3 a_maze_ing.py config.txt

処理の流れ:
    1. 設定ファイルを読む（amazeing.config）
    2. 迷路を生成する（mazegen.MazeGenerator）
    3. OUTPUT_FILE に書き出す（amazeing.output）
    4. 表示する。DISPLAY=mlx ならウィンドウ（amazeing.mlxview）、
       そうでなければ端末。標準入力が端末なら対話メニュー（amazeing.menu）
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

from amazeing.config import ConfigError, MazeConfig, load_config
from amazeing.menu import run, show
from amazeing.mlxview import MlxUnavailable, show_in_window
from amazeing.output import OutputError, write_maze
from amazeing.session import Session, report_problems
from mazegen import MazeError, MazeGenerator

USAGE = "Usage: python3 a_maze_ing.py <config file>"


def main(argv: Optional[List[str]] = None) -> int:
    """プログラムの入口。終了ステータス（成功なら 0、エラーなら 1）を返す。

    想定内のエラーはすべてここで捕まえ、"Error: ..." の 1 行を表示する。
    """
    args = sys.argv if argv is None else argv
    if len(args) != 2:
        print(USAGE, file=sys.stderr)
        return 1
    if args[1] in ("-h", "--help"):
        print(USAGE)
        return 0
    try:
        run_program(args[1])
    except (ConfigError, MazeError, OutputError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 1
    return 0


def run_program(config_path: str) -> None:
    """設定を読み、迷路を生成し、書き出して表示する。"""
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
        return
    if sys.stdin.isatty():
        run(session)
    else:
        show(session)  # パイプやリダイレクトのときは表示だけして終わる


def build_generator(config: MazeConfig) -> MazeGenerator:
    """設定の内容どおりの MazeGenerator を作る（まだ生成はしない）。

    Raises:
        MazeError: 設定では迷路を作れない場合。
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
    """端末表示で色を使うかを返す。

    設定で COLOR=False のとき、環境変数 NO_COLOR があるとき、出力が
    端末でない（ファイルやパイプ）ときは色を使わない。
    """
    return (
        config.color
        and os.environ.get("NO_COLOR") is None
        and sys.stdout.isatty()
    )


def show_window(session: Session) -> bool:
    """MiniLibX のウィンドウで表示する。使えなければ警告して False を返す。"""
    try:
        show_in_window(session)
    except MlxUnavailable as error:
        print(f"Warning: {error}", file=sys.stderr)
        print("Warning: falling back to the terminal rendering.",
              file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
