#!/usr/bin/env python3
"""A-Maze-ing -- 設定ファイルを読んで迷路を作り、書き出して端末に表示する。

使い方::

    python3 a_maze_ing.py config.txt

処理の流れ:
    1. 設定ファイルを読む（amazeing.config）
    2. 迷路を作る（mazegen.MazeGenerator）
    3. OUTPUT_FILE に書き出す（amazeing.output）
    4. 「42」を描けなかった理由と、check() で見つかった問題を表示する。
       メニューで作り直したときにも使うので、display.session.report_problems
       に置いている
    5. 端末に表示する。標準入力と標準出力がどちらも端末ならメニューを開く
       （amazeing.display）
"""

from __future__ import annotations

import sys
from typing import List, Optional

from amazeing.config import ConfigError, load_config
from amazeing.display import menu
from amazeing.display.render import can_draw_blocks
from amazeing.display.session import Session, report_problems
from amazeing.display.terminal import (
    is_terminal,
    reset_colour,
    silence_output,
)
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
        silence_output()
        return 1
    except (ConfigError, MazeError, OutputError, OSError) as error:
        reset_colour()
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        reset_colour()
        print("\nInterrupted.", file=sys.stderr)
        return 1
    except Exception as error:  # 想定外のエラーでもトレースバックは出さない
        reset_colour()
        print(f"Error: unexpected failure: {error}", file=sys.stderr)
        return 1
    return 0


def run_program(config_path: str) -> None:
    """設定を読み、迷路を生成し、書き出して表示する。"""
    config = load_config(config_path)
    # 迷路として作れない設定（大きさ、入口と出口の位置、2x2 の Pac-Man 盤）
    # なら MazeError。
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


if __name__ == "__main__":
    sys.exit(main())
