"""MiniLibX のウィンドウに迷路を表示し、キー操作で Session を動かす。"""

from __future__ import annotations

import sys
from typing import Any, Callable, List, Optional

from amazeing.minilibx import keys
from amazeing.display.canvas import draw_maze
from amazeing.minilibx.colours import token_colours
from amazeing.minilibx.setup import MlxUnavailable, choose_scale, load_mlx
from amazeing.minilibx.window import MlxWindow
from amazeing.display.session import Session

__all__ = ["MlxUnavailable", "MlxViewer", "show_in_window"]


class MlxViewer:
    """Session の迷路をウィンドウに描き、キー入力を Session の操作に変える。"""

    def __init__(
        self,
        session: Session,
        mlx_factory: Optional[Callable[[], Any]] = None,
        scale: Optional[int] = None,
    ) -> None:
        """ビューアを用意する。ウィンドウはまだ開かない。

        Args:
            session: 表示する迷路と表示設定。
            mlx_factory: MiniLibX のインスタンスを返す関数。省略すると本物の
                mlx.Mlx を読み込み、なければ MlxUnavailable。テスト用に差し替え可。
            scale: 1 マスのピクセル数。省略すると画面の大きさから決める。
        """
        self.session = session
        self.window = MlxWindow(mlx_factory or load_mlx())
        self._wanted_scale = scale
        self.scale = 0
        self.running = False
        # 作り直しても迷路の大きさは変わらないので、最初に一度だけ決める。
        self.canvas_cols = 2 * session.generator.width + 1
        self.canvas_rows = 2 * session.generator.height + 1

    def open(self) -> None:
        """画面に収まる大きさでウィンドウを開く。開けなければ MlxUnavailable。"""
        self.window.connect()
        screen_width, screen_height = 0, 0
        if self._wanted_scale is None:
            screen_width, screen_height = self.window.screen_size()
        self.scale = choose_scale(
            self.canvas_cols, self.canvas_rows,
            screen_width, screen_height, self._wanted_scale,
        )
        self.window.open(
            self.canvas_cols * self.scale,
            self.canvas_rows * self.scale,
            "A-Maze-ing",
        )

    def build_rows(self) -> List[bytes]:
        """キャンバスの各行を、画像 1 行ぶんのピクセルのバイト列にする。"""
        session = self.session
        canvas = draw_maze(session.generator, session.show_path)
        colours = token_colours(session.theme, session.pattern_colour)
        # 1 マスは横に scale ピクセル。Token ごとに 1 度だけ作っておく。
        cell_pixels = {
            token: self.window.pixel(colour) * self.scale
            for token, colour in colours.items()
        }
        return [
            b"".join(cell_pixels[token] for token in row)
            for row in canvas.cells
        ]

    def draw(self) -> None:
        """迷路と、その下のヘルプと要約を描き直す。"""
        self.window.show_rows(self.build_rows(), repeat=self.scale)
        bottom = self.window.image_height
        self.window.write(8, bottom + 10, 0xFFFFFF, keys.HELP)
        self.window.write(8, bottom + 22, 0x9AA0A6, self.session.status())

    def on_key(self, keycode: int, param: Any = None) -> None:
        """キーが押されたときに MiniLibX から呼ばれる。

        C から呼ばれる関数なので、ここから例外が漏れると ctypes に握り
        つぶされて原因が分からなくなる。すべて捕まえて表示する。
        """
        try:
            action = keys.apply_key(self.session, keycode)
            if action == keys.QUIT:
                self.close()
            elif action == keys.REDRAW:
                self.draw()
        except Exception as error:  # noqa: BLE001 - ウィンドウを生かしておく
            print(f"Error: {error}", file=sys.stderr)

    def on_close(self, param: Any = None) -> None:
        """ウィンドウの閉じるボタンが押されたときに MiniLibX から呼ばれる。"""
        self.close()

    def close(self) -> None:
        """ウィンドウを閉じ、イベントループを抜ける。"""
        self.window.close()
        self.running = False

    def run(self) -> None:
        """ウィンドウを開いて迷路を描き、閉じられるまで待つ。"""
        self.open()
        print(f"MiniLibX window -- {keys.HELP}")
        self.draw()
        self.window.listen(self.on_key, self.on_close)
        self.running = True
        try:
            self.window.loop()
        except KeyboardInterrupt:
            self.close()
        finally:
            self.running = False


def show_in_window(session: Session) -> None:
    """session の迷路を MiniLibX のウィンドウで表示する。

    Raises:
        MlxUnavailable: MiniLibX を使えない場合。
    """
    MlxViewer(session).run()
