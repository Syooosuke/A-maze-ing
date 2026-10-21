"""MiniLibX ウィンドウのキー操作。端末メニューと同じ番号を割り当てる。"""

from __future__ import annotations

from amazeing.session import Session

# キーの X11 keysym。
KEY_REGENERATE = 0x31  # '1'
KEY_PATH = 0x32        # '2'
KEY_COLOURS = 0x33     # '3'
KEY_PATTERN = 0x34     # '4'
KEY_SAVE = 0x35        # '5'
KEY_QUIT = 0x36        # '6'
KEY_Q = 0x71           # 'q'
KEY_ESCAPE = 0xFF1B    # Esc
QUIT_KEYS = (KEY_QUIT, KEY_Q, KEY_ESCAPE)

HELP = "1: regen   2: path   3: colours   4: 42   5: save   6/Esc: quit"

# apply_key() の結果。キーを処理した後にビューアがすること。
QUIT = "quit"
REDRAW = "redraw"
NOTHING = "nothing"


def apply_key(session: Session, keycode: int) -> str:
    """keycode に割り当てた操作を session に行い、次にすることを返す。

    Returns:
        QUIT（ウィンドウを閉じる）、REDRAW（描き直す）、NOTHING のどれか。
        割り当てのないキーは NOTHING。
    """
    if keycode in QUIT_KEYS:
        return QUIT
    if keycode == KEY_REGENERATE:
        return REDRAW if session.regenerate() else NOTHING
    if keycode == KEY_PATH:
        session.toggle_path()
        return REDRAW
    if keycode == KEY_COLOURS:
        session.next_theme()
        return REDRAW
    if keycode == KEY_PATTERN:
        session.toggle_pattern_colour()
        return REDRAW
    if keycode == KEY_SAVE:
        session.save()
    return NOTHING
