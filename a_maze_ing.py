#!/usr/bin/env python3
"""A-Maze-ing -- 設定ファイルから迷路を生成し、保存して表示する。

使い方::

    python3 a_maze_ing.py config.txt

処理の流れ:
    1. 設定ファイルを読む（amazeing.config）
    2. 迷路を生成する（mazegen.MazeGenerator）
    3. OUTPUT_FILE に書き出し（amazeing.output）、要件を自己検査した結果を
       表示する（MazeGenerator.check() を display.session.report_problems
       から呼ぶ。作り直したときも同じ関数を使うので display にある）
    4. 端末に表示する。入力も出力も端末なら対話メニューを開く
       （amazeing.display）
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, TextIO

from amazeing.config import ConfigError, load_config
from amazeing.display import menu
from amazeing.display.render import can_draw_blocks
from amazeing.display.session import Session, report_problems
from amazeing.output import OutputError, write_maze
from mazegen import MazeError, MazeGenerator

USAGE: str = "Usage: python3 a_maze_ing.py <config file>"


def main(argv: Optional[List[str]] = None) -> int:
    """プログラムの入口。終了ステータス（成功なら 0、エラーなら 1）を返す。

    エラーはすべてここで捕まえ、トレースバックを出さずに 1 行で知らせる。
    出力先のパイプが先に閉じられたときだけは、何も表示せずに終わる。
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
        if sys.stdout is not None:
            sys.stdout.flush()  # 書き出しの失敗を、ここで捕まえるため
    except BrokenPipeError:
        _silence_output()
        return 1
    except (ConfigError, MazeError, OutputError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 1
    except Exception as error:  # 想定外のエラーでもトレースバックは出さない
        print(f"Error: unexpected failure: {error}", file=sys.stderr)
        return 1
    return 0


def run_program(config_path: str) -> None:
    """設定を読み、迷路を生成し、書き出して表示する。"""
    config = load_config(config_path)
    # 迷路として作れない設定（大きさ、入口と出口の位置）なら MazeError。
    generator = MazeGenerator(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.perfect,
        seed=config.seed,
    )
    generator.generate()
    write_maze(config.output_file, generator)
    print(f"Maze written to {config.output_file}")
    report_problems(generator)  # "42" を描けなかった理由と check() の結果

    # 出力が端末でない（ファイルやパイプ）ときや、端末が "██" を表示でき
    # ないときは、色を使わず ASCII で描く。
    colour = is_terminal(sys.stdout) and can_draw_blocks(sys.stdout.encoding)
    session = Session(generator, colour=colour)
    if is_terminal(sys.stdin) and is_terminal(sys.stdout):
        menu.run(session)
    else:
        menu.show(session)  # パイプやリダイレクトのときは表示だけして終わる


def is_terminal(stream: Optional[TextIO]) -> bool:
    """stream が端末につながっているかを返す。

    標準入出力が閉じられていると、Python はそれを None にする。
    """
    return stream is not None and stream.isatty()


def _silence_output() -> None:
    """出力先のパイプが先に閉じられたときに、標準出力と標準エラーを捨てる。

    そのままだと、終了時に Python が出力を flush し直し、BrokenPipeError
    の警告を出して終了ステータス 120 で終わる。/dev/null に向け直して防ぐ。
    """
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        for stream in (sys.stdout, sys.stderr):
            try:
                os.dup2(devnull, stream.fileno())
            except (AttributeError, OSError, ValueError):
                pass  # 閉じられている（None）か、本物のファイルではない
    finally:
        os.close(devnull)


if __name__ == "__main__":
    sys.exit(main())
