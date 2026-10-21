"""標準入出力と端末まわりの小さな処理。"""

from __future__ import annotations

import os
import sys
from typing import Optional, TextIO

from amazeing.display.render import RESET


def is_terminal(stream: Optional[TextIO]) -> bool:
    """stream が端末につながっているかを返す。

    標準入出力が閉じられていると、Python はそれを None にする。
    """
    return stream is not None and stream.isatty()


def reset_colour() -> None:
    """色付きの描画の途中で止まったときに、端末の色を元に戻す。"""
    if is_terminal(sys.stdout):
        try:
            sys.stdout.write(RESET)
            sys.stdout.flush()
        except OSError:
            pass


def silence_output() -> None:
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
