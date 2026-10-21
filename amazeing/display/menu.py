"""端末で動く対話メニュー。番号を入力して迷路を操作する。"""

from __future__ import annotations

from typing import Optional

from amazeing.display.session import Session

MENU = (
    "1. Re-generate a new maze",
    "2. Show / Hide the shortest path",
    "3. Rotate the wall colours",
    "4. Quit",
)
# 終了の番号はメニューの最後の項目。項目を足しても自動でずれる。
QUIT_WORDS = (str(len(MENU)), "q", "quit")


def show(session: Session) -> None:
    """迷路と凡例と要約を表示する。"""
    print(session.screen())


def run(session: Session) -> None:
    """迷路を表示し、利用者が終了を選ぶまでメニューを繰り返す。"""
    show(session)
    while True:
        choice = _ask_choice()
        if choice is None or choice in QUIT_WORDS:
            print("Bye!")
            return
        if _apply(session, choice):
            show(session)


def _ask_choice() -> Optional[str]:
    """メニューを表示して 1 つ選んでもらう。入力が終わったら None。"""
    print()
    print("=== A-Maze-ing ===")
    for line in MENU:
        print(line)
    try:
        return input(f"Choice? (1-{len(MENU)}): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _apply(session: Session, choice: str) -> bool:
    """選ばれた項目を実行する。迷路を描き直すべきなら True を返す。"""
    if choice == "1":
        return session.regenerate()
    if choice == "2":
        session.toggle_path()
        return True
    if choice == "3":
        session.next_theme()
        return True
    print(f"Unknown choice {choice!r}, please pick 1 to {len(MENU)}.")
    return False
