"""表示中の迷路と、表示の設定（配色、経路の表示など）を保持する。

端末のメニューと MiniLibX のウィンドウは、どちらもこの Session を
操作する。キー入力やメニューの番号から、ここのメソッドを呼ぶだけ。
"""

from __future__ import annotations

import sys

from amazeing.config import MazeConfig
from amazeing.output import OutputError, write_maze
from amazeing.render import legend, render
from amazeing.themes import THEMES, Theme
from mazegen import MazeError, MazeGenerator, random_seed


class Session:
    """表示中の迷路と、利用者が切り替えられる表示の設定。"""

    def __init__(self, generator: MazeGenerator, config: MazeConfig) -> None:
        """generate() を呼び終えた generator を表示する準備をする。"""
        self.generator = generator
        self.config = config
        self.theme_index = 0
        self.show_path = False
        self.pattern_colour = True
        self.colour = config.color

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

    def toggle_pattern_colour(self) -> None:
        """"42" を専用の色で描くか、壁と同じ色で描くかを切り替える。"""
        self.pattern_colour = not self.pattern_colour

    def save(self) -> None:
        """いまの迷路を、設定ファイルの OUTPUT_FILE に書き出す。"""
        path = self.config.output_file
        try:
            write_maze(path, self.generator)
        except OutputError as error:
            print(f"Error: {error}", file=sys.stderr)
            return
        print(f"Maze written to {path}")

    def status(self) -> str:
        """いまの迷路の要約を 1 行で返す（大きさ、モード、シードなど）。"""
        maze = self.generator
        mode = "perfect" if maze.perfect else "playable board"
        return (
            f"{maze.width}x{maze.height} - {mode} - {maze.algorithm} - "
            f"seed {maze.seed_used} - path {len(maze.solution)} cells - "
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
            pattern_colour=self.pattern_colour,
        )
        key = legend(self.theme, self.colour, self.pattern_colour)
        return "\n".join((picture, "", key, self.status()))


def report_problems(generator: MazeGenerator) -> None:
    """迷路が要件を満たしていない点があれば、警告として表示する。"""
    for problem in generator.check():
        print(f"Warning: {problem}", file=sys.stderr)
