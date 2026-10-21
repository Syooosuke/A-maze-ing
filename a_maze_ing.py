#!/usr/bin/env python3
"""A-Maze-ing -- 設定ファイルから迷路を生成し、保存して表示する。

使い方::

    python3 a_maze_ing.py config.txt

処理の流れ:
    1. 設定ファイルを読む（amazeing.config）
    2. 迷路を生成し、要件を自己検査した結果を表示する
       （mazegen.MazeGenerator.check() を display.session.report_problems
       から呼ぶ。作り直したときも同じ関数を使うので display にある）
    3. OUTPUT_FILE に書き出す（amazeing.output）
    4. 端末に表示する。入力も出力も端末なら対話メニューを開く
       （amazeing.display）
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, TextIO

from amazeing.config import ConfigError, MazeConfig, load_config
from amazeing.display import menu
from amazeing.display.render import can_draw_blocks
from amazeing.display.session import Session, report_problems
from amazeing.output import OutputError, write_maze
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
        if sys.stdout is not None:
            sys.stdout.flush()  # 書き出しの失敗を、ここで捕まえるため
    except BrokenPipeError:
        # 出力先（パイプ）が先に閉じられた。もう何も表示できないので、
        # 終了時に Python が出す警告も防ぐため、標準出力を捨て先に向ける。
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
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
    generator = build_generator(config)
    generator.generate()
    report_problems(generator)  # "42" を描けなかった理由と check() の結果

    write_maze(config.output_file, generator)
    print(f"Maze written to {config.output_file}")

    # 出力が端末でない（ファイルやパイプ）ときや、端末が "██" を表示でき
    # ないときは、色を使わず ASCII で描く。
    stdout = sys.stdout
    colour = (
        stdout is not None and stdout.isatty()
        and can_draw_blocks(stdout.encoding)
    )
    session = Session(generator, colour=colour)
    if is_terminal(sys.stdin) and is_terminal(sys.stdout):
        menu.run(session)
    else:
        menu.show(session)  # パイプやリダイレクトのときは表示だけして終わる


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
    )


def is_terminal(stream: Optional[TextIO]) -> bool:
    """stream が端末につながっているかを返す。

    標準入出力が閉じられていると、Python はそれを None にする。
    """
    return stream is not None and stream.isatty()


if __name__ == "__main__":
    sys.exit(main())
