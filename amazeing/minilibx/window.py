"""MiniLibX のウィンドウ 1 枚と画像 1 枚の作成・描画・破棄。

迷路のことは知らない。渡されたピクセルの行や文字列を描くだけ。
"""

from __future__ import annotations

import sys
from typing import Any, Callable, List, Tuple

from amazeing.minilibx.setup import FOOTER_HEIGHT, MlxUnavailable

# ウィンドウの閉じるボタンを捕まえるための X11 のイベント番号とマスク。
DESTROY_NOTIFY = 17
STRUCTURE_NOTIFY_MASK = 1 << 17


class MlxWindow:
    """ウィンドウ 1 枚と、迷路を描き込む画像 1 枚。

    1 ピクセルずつ mlx_pixel_put で描くと遅いので、画像のメモリに直接
    書き込み、mlx_put_image_to_window で一度に転送する。
    """

    def __init__(self, mlx_factory: Callable[[], Any]) -> None:
        """mlx_factory() は MiniLibX のインスタンスを返す（テストでは偽物）。"""
        self._factory = mlx_factory
        self.mlx: Any = None
        self.mlx_ptr: Any = None
        self.win_ptr: Any = None
        self.img_ptr: Any = None
        self.image_width = 0
        self.image_height = 0
        self._buffer: Any = None
        self.bytes_per_pixel = 4
        self._bytes_per_line = 0

    def connect(self) -> None:
        """MiniLibX を初期化する。ディスプレイがなければ MlxUnavailable。"""
        self.mlx = self._factory()
        self.mlx_ptr = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise MlxUnavailable(
                "mlx_init() failed: no display available (is DISPLAY set?)"
            )

    def screen_size(self) -> Tuple[int, int]:
        """画面の (幅, 高さ) を返す。分からなければ (0, 0)。"""
        try:
            _, width, height = self.mlx.mlx_get_screen_size(self.mlx_ptr)
        except Exception:  # noqa: BLE001 - 実装によっては未対応
            return 0, 0
        return int(width or 0), int(height or 0)

    def open(self, width: int, height: int, title: str) -> None:
        """width x height の画像と、下に余白を足したウィンドウを作る。

        作れなければ MlxUnavailable を送出する。
        """
        self.image_width, self.image_height = width, height
        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, width, height + FOOTER_HEIGHT, title
        )
        if not self.win_ptr:
            raise MlxUnavailable("mlx_new_window() failed")
        self.img_ptr = self.mlx.mlx_new_image(self.mlx_ptr, width, height)
        if not self.img_ptr:
            raise MlxUnavailable("mlx_new_image() failed")
        buffer, bits_per_pixel, bytes_per_line, _ = (
            self.mlx.mlx_get_data_addr(self.img_ptr)
        )
        self._buffer = buffer
        self.bytes_per_pixel = max(1, int(bits_per_pixel) // 8)
        self._bytes_per_line = int(bytes_per_line)

    def pixel(self, colour: int) -> bytes:
        """RGB 色を、画像のメモリに書く 1 ピクセルぶんのバイト列にする。"""
        return colour.to_bytes(4, sys.byteorder)[: self.bytes_per_pixel]

    def show_rows(self, rows: List[bytes], repeat: int) -> None:
        """rows の各行を repeat 回ずつ縦に並べて画像に書き、ウィンドウに出す。"""
        stride = self._bytes_per_line
        if not stride:
            stride = self.image_width * self.bytes_per_pixel
        for index, row in enumerate(rows):
            for copy in range(repeat):
                start = (index * repeat + copy) * stride
                self._buffer[start:start + len(row)] = row
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
        )

    def write(self, x: int, y: int, colour: int, text: str) -> None:
        """ウィンドウの (x, y) に文字列を書く。"""
        self.mlx.mlx_string_put(self.mlx_ptr, self.win_ptr, x, y, colour, text)

    def listen(
        self,
        on_key: Callable[[int, Any], None],
        on_close: Callable[[Any], None],
    ) -> None:
        """キーが押されたら on_key を、閉じるボタンでは on_close を呼ばせる。"""
        self.mlx.mlx_key_hook(self.win_ptr, on_key, None)
        self.mlx.mlx_hook(
            self.win_ptr, DESTROY_NOTIFY, STRUCTURE_NOTIFY_MASK, on_close, None
        )

    def loop(self) -> None:
        """close() が呼ばれるまで、イベントを待ち続ける。"""
        self.mlx.mlx_loop(self.mlx_ptr)

    def close(self) -> None:
        """画像とウィンドウを破棄し、イベントループを抜ける。"""
        if self.mlx is None:
            return
        try:
            if self.img_ptr:
                self.mlx.mlx_destroy_image(self.mlx_ptr, self.img_ptr)
                self.img_ptr = None
            if self.win_ptr:
                self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
                self.win_ptr = None
            self.mlx.mlx_loop_exit(self.mlx_ptr)
        except Exception as error:  # noqa: BLE001 - 後片付けでは落ちない
            print(f"Warning: MiniLibX cleanup failed: {error}",
                  file=sys.stderr)
