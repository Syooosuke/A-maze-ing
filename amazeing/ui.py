"""迷路生成器の対話的な端末フロントエンド。"""

from __future__ import annotations

import random
import sys
from typing import List, Optional

from amazeing.config import MazeConfig
from amazeing.output import OutputError, write_maze
from amazeing.render import THEMES, Theme, legend, render
from mazegen import MazeError, MazeGenerator

_MENU = (
    "1. Re-generate a new maze",
    "2. Show / Hide the shortest path",
    "3. Rotate the wall colours",
    '4. Toggle the "42" colours',
    "5. Save the maze to the output file",
    "6. Quit",
)


class Session:
    """対話実行中の迷路と表示オプションを保持する。"""

    def __init__(
        self, generator: MazeGenerator, config: MazeConfig
    ) -> None:
        """生成済みの迷路を包むセッションを用意する。

        Args:
            generator: ``generate()`` を呼び終えた生成器。
            config: その迷路を作るのに使った設定。
        """
        self.generator = generator
        self.config = config
        self.theme_index = 0
        self.show_path = False
        self.pattern_colour = True
        self.colour = config.color

    @property
    def theme(self) -> Theme:
        """いま迷路の描画に使っているテーマを返す。"""
        return THEMES[self.theme_index]

    def regenerate(self) -> None:
        """新しい乱数シードで迷路を作り直す。

        Raises:
            MazeError: 新しい迷路を作れない場合。
        """
        self.generator.generate(seed=random.randrange(2 ** 32))

    def toggle_path(self) -> None:
        """最短経路の表示と非表示を切り替える。"""
        self.show_path = not self.show_path

    def next_theme(self) -> None:
        """次の配色に切り替える。"""
        self.theme_index = (self.theme_index + 1) % len(THEMES)

    def toggle_pattern_colour(self) -> None:
        """パターン "42" に専用色を与えるか、壁と同じ色にするか。"""
        self.pattern_colour = not self.pattern_colour

    def save(self) -> None:
        """いまの迷路を設定された出力ファイルに書き出す。"""
        path = self.config.output_file
        try:
            write_maze(path, self.generator)
        except OutputError as error:
            print(f"Error: {error}", file=sys.stderr)
            return
        print(f"Maze written to {path}")

    def status(self) -> str:
        """いまの迷路の要約を 1 行で返す。"""
        generator = self.generator
        mode = "perfect" if generator.perfect else "playable board"
        return (
            f"{generator.width}x{generator.height} - {mode} - "
            f"{generator.algorithm} - seed {generator.seed_used} - "
            f"path {len(generator.solution)} cells - "
            f"{generator.loop_count()} loop(s) - "
            f"{len(generator.dead_ends())} dead-end(s)"
        )

    def screen(self) -> str:
        """画面全体、つまり迷路と凡例と状態行をまとめて返す。"""
        picture = render(
            self.generator,
            theme=self.theme,
            show_path=self.show_path,
            colour=self.colour,
            pattern_colour=self.pattern_colour,
        )
        return "\n".join(
            (
                picture,
                "",
                legend(self.theme, self.colour, self.pattern_colour),
                self.status(),
            )
        )


def report_problems(generator: MazeGenerator) -> None:
    """迷路が満たしていない要件を標準エラー出力に表示する。"""
    problems: List[str] = generator.check()
    for problem in problems:
        print(f"Warning: {problem}", file=sys.stderr)


def show(session: Session) -> None:
    """迷路と、その周りの情報を表示する。"""
    print(session.screen())


def _prompt() -> Optional[str]:
    """メニューを表示して選択を 1 つ読む。入力終了なら ``None``。"""
    print()
    print("=== A-Maze-ing ===")
    for entry in _MENU:
        print(entry)
    try:
        return input(f"Choice? (1-{len(_MENU)}): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _apply(session: Session, choice: str) -> bool:
    """メニューの選択を 1 つ実行する。

    Args:
        session: 迷路と表示オプションを保持するセッション。
        choice: 利用者が入力した項目。

    Returns:
        迷路を描き直す必要があるなら ``True``。
    """
    if choice == "1":
        try:
            session.regenerate()
        except MazeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return False
        report_problems(session.generator)
    elif choice == "2":
        session.toggle_path()
    elif choice == "3":
        session.next_theme()
    elif choice == "4":
        session.toggle_pattern_colour()
    elif choice == "5":
        session.save()
        return False
    else:
        print(f"Unknown choice {choice!r}, please pick 1 to {len(_MENU)}.")
        return False
    return True


def run(session: Session) -> None:
    """利用者が終了を選ぶまで対話メニューを回す。

    Args:
        session: 迷路と表示オプションを保持するセッション。
    """
    show(session)
    while True:
        choice = _prompt()
        if choice is None or choice in ("6", "q", "quit"):
            print("Bye!")
            return
        if _apply(session, choice):
            show(session)
