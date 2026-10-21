"""キャンバスを端末に表示できる文字列にする（ANSI カラー、または ASCII）。"""

from __future__ import annotations

from itertools import groupby
from typing import Dict, List, Optional

from amazeing.display.canvas import Token, draw_maze
from amazeing.display.themes import THEMES, Theme
from mazegen import MazeGenerator

# 色を使わないときの描き方。1 マスを 2 文字で描くと、端末でほぼ正方形になる。
ASCII: Dict[Token, str] = {
    Token.VOID: "  ",
    Token.WALL: "##",
    Token.PATTERN: "%%",
    Token.PATH: "..",
    Token.ENTRY: "EE",
    Token.EXIT: "XX",
}

# 色を使うときは、どのマスもこのブロック文字を色付けして描く。
BLOCK = "██"
RESET = "\x1b[0m"


def can_draw_blocks(encoding: Optional[str]) -> bool:
    """その文字コードの端末で BLOCK を表示できるかを返す。"""
    try:
        BLOCK.encode(encoding or "ascii")
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def colour_of(token: Token, theme: Theme) -> int:
    """token を描く 256 色番号を返す。"""
    if token is Token.PATTERN:
        return theme.pattern
    if token is Token.PATH:
        return theme.path
    if token is Token.ENTRY:
        return theme.entry
    if token is Token.EXIT:
        return theme.exit
    return theme.wall


def swatch(token: Token, theme: Theme, colour: bool, count: int = 1) -> str:
    """同じ token のマスを count 個、横に並べて描いた文字列を返す。

    colour が False なら ASCII 文字で描く。空白のマスは常に空白のまま。
    """
    if not colour or token is Token.VOID:
        return ASCII[token] * count
    code = colour_of(token, theme)
    # \x1b[38;5;<番号>m は、文字色を 256 色の <番号> にする ANSI コード。
    return f"\x1b[38;5;{code}m{BLOCK * count}{RESET}"


def _render_row(row: List[Token], theme: Theme, colour: bool) -> str:
    """キャンバスの 1 行を文字列にする。同じ Token が続く部分はまとめる。"""
    return "".join(
        swatch(token, theme, colour, count=len(list(run)))
        for token, run in groupby(row)
    )


def render(
    generator: MazeGenerator,
    theme: Theme = THEMES[0],
    show_path: bool = False,
    colour: bool = True,
) -> str:
    """迷路全体を、端末にそのまま表示できる文字列にする。

    Args:
        generator: generate() を呼び終えた生成器。
        theme: 配色。
        show_path: 入口から出口までの最短経路を描くかどうか。
        colour: ANSI カラーを使うかどうか。False なら ASCII 文字で描く。

    Returns:
        描いた迷路。末尾に改行は付かない。
    """
    canvas = draw_maze(generator, show_path)
    return "\n".join(_render_row(row, theme, colour) for row in canvas.cells)


def legend(theme: Theme, colour: bool) -> str:
    """いまの配色での、各マスの意味を 1 行で返す。"""
    items = (
        (Token.ENTRY, "entry"),
        (Token.EXIT, "exit"),
        (Token.PATTERN, "42"),
        (Token.PATH, "path"),
        (Token.WALL, "wall"),
    )
    return "  ".join(
        f"{swatch(token, theme, colour)} {label}" for token, label in items
    )
