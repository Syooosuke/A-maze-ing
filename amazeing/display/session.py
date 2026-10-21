"""表示中の迷路と、表示の設定（配色、経路の表示）を保持する。

端末のメニューは、選ばれた番号に応じてここのメソッドを呼ぶだけ。
"""

from __future__ import annotations

import sys

from amazeing.display.render import legend, render
from amazeing.display.themes import THEMES, Theme
from mazegen import MazeError, MazeGenerator, random_seed


class Session:
    """表示中の迷路と、利用者が切り替えられる表示の設定。"""

    def __init__(self, generator: MazeGenerator, colour: bool) -> None:
        """generate() を呼び終えた generator を表示する準備をする。

        Args:
            generator: 表示する迷路。
            colour: ANSI カラーで描くかどうか。False なら ASCII 文字で描く。
        """
        self.generator = generator
        self.colour = colour
        self.theme_index = 0
        self.show_path = False

    @property
    def theme(self) -> Theme:
        """いまの配色を返す。"""
        return THEMES[self.theme_index]

    def regenerate(self) -> bool:
        """新しいランダムなシードで迷路を作り直す。

        Returns:
            作り直せたら True。作れなかったらエラーを表示して False。
        """
        try:
            self.generator.generate(seed=random_seed())
        except MazeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return False
        report_problems(self.generator)
        return True

    def toggle_path(self) -> None:
        """最短経路の表示と非表示を切り替える。"""
        self.show_path = not self.show_path

    def next_theme(self) -> None:
        """次の配色に切り替える。最後の次は最初に戻る。"""
        self.theme_index = (self.theme_index + 1) % len(THEMES)

    def status(self) -> str:
        """いまの迷路の要約を 1 行で返す（大きさ、モード、シードなど）。"""
        maze = self.generator
        mode = "perfect" if maze.perfect else "playable board"
        return (
            f"{maze.width}x{maze.height} - {mode} - "
            f"theme {self.theme.name} - seed {maze.seed_used} - "
            f"path {len(maze.solution)} cells - "
            f"{maze.loop_count()} loop(s) - "
            f"{len(maze.dead_ends())} dead-end(s)"
        )

    def screen(self) -> str:
        """端末に表示する画面全体（迷路、凡例、要約）を返す。"""
        picture = render(
            self.generator,
            theme=self.theme,
            show_path=self.show_path,
            colour=self.colour,
        )
        key = legend(self.theme, self.colour)
        return "\n".join((picture, "", key, self.status()))


def report_problems(generator: MazeGenerator) -> None:
    """「42」を描けなかった理由と、要件を満たしていない点を表示する。

    起動時と、メニューで迷路を作り直したときの両方から呼ばれる。
    """
    if generator.pattern_warning is not None:
        # subject が「エラーメッセージを表示する」と書いているので Error とする。
        # 迷路そのものは作れているので、終了ステータスは 0 のまま。
        print(
            f"Error: {generator.pattern_warning}; "
            "the maze is generated without it",
            file=sys.stderr,
        )
    for problem in generator.check():
        print(f"Warning: {problem}", file=sys.stderr)
