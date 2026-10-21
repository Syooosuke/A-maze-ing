"""MiniLibX ウィンドウで使う色。端末と同じ配色を RGB に変換する。"""

from __future__ import annotations

from typing import Dict

from amazeing.canvas import Token
from amazeing.render import colour_of
from amazeing.themes import Theme

# 迷路の通路（何もないマス）の色。
BACKGROUND = 0x101014

# xterm の 256 色のうち、最初の 16 色。
BASE_COLOURS = (
    0x000000, 0x800000, 0x008000, 0x808000,
    0x000080, 0x800080, 0x008080, 0xC0C0C0,
    0x808080, 0xFF0000, 0x00FF00, 0xFFFF00,
    0x0000FF, 0xFF00FF, 0x00FFFF, 0xFFFFFF,
)
# 16〜231 番は 6x6x6 の色立方体。各成分はこの 6 段階のどれか。
CUBE_LEVELS = (0, 95, 135, 175, 215, 255)


def ansi256_to_rgb(index: int) -> int:
    """xterm の 256 色番号を 0xRRGGBB に変換する。

    Theme は端末用に 256 色番号で色を持っているので、ウィンドウに描く
    前にこの変換が要る。
    """
    if index < 16:
        return BASE_COLOURS[index]
    if index < 232:
        # 16 を引いた値を 6 進数 3 桁とみなすと、各桁が赤・緑・青の段階。
        offset = index - 16
        red = CUBE_LEVELS[offset // 36]
        green = CUBE_LEVELS[(offset // 6) % 6]
        blue = CUBE_LEVELS[offset % 6]
        return (red << 16) | (green << 8) | blue
    # 232〜255 番は、黒に近い灰色から白に近い灰色までの 24 段階。
    grey = 8 + 10 * (index - 232)
    return (grey << 16) | (grey << 8) | grey


def token_colours(theme: Theme, pattern_colour: bool) -> Dict[Token, int]:
    """キャンバスの各 Token を描く RGB 色の対応表を返す。"""
    colours = {
        token: ansi256_to_rgb(colour_of(token, theme, pattern_colour))
        for token in Token
    }
    colours[Token.VOID] = BACKGROUND
    return colours
