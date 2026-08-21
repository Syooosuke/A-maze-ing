"""MiniLibX ライブラリによる、任意機能のグラフィカルな迷路描画。

``mlx`` パッケージ（subject に ``mlx-2.2.tgz`` として同梱）は、C 版の
MiniLibX を ctypes で薄く包んだものである。これは本プロジェクトの依存
関係では **ない**。見つからないときや利用できるディスプレイがないとき
は、はっきりしたメッセージを出したうえで端末描画へ切り替える。

迷路全体は 1 枚の MiniLibX 画像に描き、それを 1 回の呼び出しで転送する。
``mlx_pixel_put`` で 1 ピクセルずつ描く方法は、数百セルの迷路には遅すぎ
るからである。
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Dict, List, Optional

from amazeing.render import Canvas, Theme, Token
from amazeing.ui import Session
from mazegen import MazeError

# X11 keysyms of the keys driving the viewer.
KEY_REGENERATE = 0x31  # '1'
KEY_PATH = 0x32        # '2'
KEY_COLOURS = 0x33     # '3'
KEY_PATTERN = 0x34     # '4'
KEY_SAVE = 0x35        # '5'
KEY_QUIT = 0x36        # '6'
KEY_Q = 0x71           # 'q'
KEY_ESCAPE = 0xFF1B    # Escape

# X11 DestroyNotify, used to catch a click on the window close button.
_DESTROY_NOTIFY = 17
_STRUCTURE_NOTIFY_MASK = 1 << 17

_FOOTER_HEIGHT = 26
_MIN_SCALE = 2
_MAX_SCALE = 16
_DEFAULT_SCALE = 8

_HELP = "1: regen   2: path   3: colours   4: 42   5: save   6/Esc: quit"

# The six levels of the xterm 6x6x6 colour cube.
_CUBE_LEVELS = (0, 95, 135, 175, 215, 255)
# The sixteen basic xterm colours.
_BASE_COLOURS = (
    0x000000, 0x800000, 0x008000, 0x808000,
    0x000080, 0x800080, 0x008080, 0xC0C0C0,
    0x808080, 0xFF0000, 0x00FF00, 0xFFFF00,
    0x0000FF, 0xFF00FF, 0x00FFFF, 0xFFFFFF,
)

_BACKGROUND = 0x101014


class MlxUnavailable(Exception):
    """この環境で MiniLibX を使えないときに送出する。"""


def ansi256_to_rgb(index: int) -> int:
    """xterm の 256 色番号を ``0xRRGGBB`` の値に変換する。

    端末描画とグラフィカル描画は同じ :class:`~amazeing.render.Theme` を
    共有しているので、ANSI エスケープシーケンス用のパレットから色を
    変換する必要がある。

    Args:
        index: 0 から 255 までの色番号。

    Returns:
        対応する 24 ビットの RGB 色。
    """
    if index < 16:
        return _BASE_COLOURS[index]
    if index < 232:
        offset = index - 16
        red = _CUBE_LEVELS[offset // 36]
        green = _CUBE_LEVELS[(offset // 6) % 6]
        blue = _CUBE_LEVELS[offset % 6]
        return (red << 16) | (green << 8) | blue
    grey = 8 + 10 * (index - 232)
    return (grey << 16) | (grey << 8) | grey


def load_mlx() -> Any:
    """MiniLibX のラッパーを読み込む。

    Returns:
        ``mlx.Mlx`` クラス。

    Raises:
        MlxUnavailable: パッケージまたは共有ライブラリが見つからない
            場合。
    """
    try:
        from mlx import Mlx
    except ImportError as error:
        raise MlxUnavailable(
            "the 'mlx' package is not installed "
            f"(pip install mlx-2.2-py3-none-any.whl): {error}"
        ) from None
    except OSError as error:
        raise MlxUnavailable(
            f"the MiniLibX shared library cannot be loaded: {error}"
        ) from None
    return Mlx


class MlxViewer:
    """MiniLibX のウィンドウに迷路を表示し、キー入力を処理する。"""

    def __init__(
        self,
        session: Session,
        mlx_factory: Optional[Callable[[], Any]] = None,
        scale: Optional[int] = None,
    ) -> None:
        """``session`` を表示するビューアを用意する。

        Args:
            session: 迷路と表示オプションを保持するセッション。
            mlx_factory: MiniLibX のインスタンスを返す呼び出し可能
                オブジェクト。既定では本物の ``mlx.Mlx`` クラスを使う。
                ここにテスト用の代役を差し込めるおかげで、ディスプレイ
                なしでもビューアを試験できる。
            scale: 半セル 1 つのピクセル数。省略すると画面サイズから
                計算する。
        """
        self.session = session
        self._factory: Callable[[], Any] = (
            mlx_factory if mlx_factory is not None else load_mlx()
        )
        self._wanted_scale = scale
        self.mlx: Any = None
        self.mlx_ptr: Any = None
        self.win_ptr: Any = None
        self.img_ptr: Any = None
        self.scale = _DEFAULT_SCALE
        self.running = False
        self._buffer: Any = None
        self._bytes_per_pixel = 4
        self._size_line = 0

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    @property
    def canvas_cols(self) -> int:
        """キャンバスの横方向の半セル数。"""
        return 2 * self.session.generator.width + 1

    @property
    def canvas_rows(self) -> int:
        """キャンバスの縦方向の半セル数。"""
        return 2 * self.session.generator.height + 1

    @property
    def image_width(self) -> int:
        """迷路画像の幅（ピクセル）。"""
        return self.canvas_cols * self.scale

    @property
    def image_height(self) -> int:
        """迷路画像の高さ（ピクセル）。"""
        return self.canvas_rows * self.scale

    def _pick_scale(self) -> int:
        """画面に収まる範囲で最大の半セルサイズを選ぶ。"""
        if self._wanted_scale is not None:
            return max(1, self._wanted_scale)
        try:
            _, screen_w, screen_h = self.mlx.mlx_get_screen_size(self.mlx_ptr)
        except Exception:  # noqa: BLE001 - any backend may refuse this
            return _DEFAULT_SCALE
        if not screen_w or not screen_h:
            return _DEFAULT_SCALE
        usable_h = int(screen_h) - _FOOTER_HEIGHT - 80
        scale = min(
            (int(screen_w) - 40) // self.canvas_cols,
            usable_h // self.canvas_rows,
        )
        return max(_MIN_SCALE, min(_MAX_SCALE, scale))

    # ------------------------------------------------------------------
    # Colours
    # ------------------------------------------------------------------
    def _palette(self) -> Dict[Token, int]:
        """キャンバスの各トークンを 24 ビットの RGB 色に対応付ける。"""
        theme: Theme = self.session.theme
        pattern = (
            theme.pattern if self.session.pattern_colour else theme.wall
        )
        return {
            Token.VOID: _BACKGROUND,
            Token.WALL: ansi256_to_rgb(theme.wall),
            Token.PATTERN: ansi256_to_rgb(pattern),
            Token.PATH: ansi256_to_rgb(theme.path),
            Token.ENTRY: ansi256_to_rgb(theme.entry),
            Token.EXIT: ansi256_to_rgb(theme.exit),
        }

    def _pixel_bytes(self, colour: int) -> bytes:
        """MiniLibX の画像が期待する形式で色を符号化する。"""
        return colour.to_bytes(4, sys.byteorder)[: self._bytes_per_pixel]

    # ------------------------------------------------------------------
    # Window life cycle
    # ------------------------------------------------------------------
    def open(self) -> None:
        """ウィンドウと画像を作る。

        Raises:
            MlxUnavailable: ディスプレイまたは画像を用意できない場合。
        """
        self.mlx = self._factory()
        self.mlx_ptr = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise MlxUnavailable(
                "mlx_init() failed: no display available "
                "(is DISPLAY set?)"
            )
        self.scale = self._pick_scale()
        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr,
            self.image_width,
            self.image_height + _FOOTER_HEIGHT,
            "A-Maze-ing",
        )
        if not self.win_ptr:
            raise MlxUnavailable("mlx_new_window() failed")
        self._new_image()

    def _new_image(self) -> None:
        """迷路を描き込むための画像を確保する。

        Raises:
            MlxUnavailable: 画像を作れない場合。
        """
        self.img_ptr = self.mlx.mlx_new_image(
            self.mlx_ptr, self.image_width, self.image_height
        )
        if not self.img_ptr:
            raise MlxUnavailable("mlx_new_image() failed")
        buffer, bits_per_pixel, size_line, _ = self.mlx.mlx_get_data_addr(
            self.img_ptr
        )
        self._buffer = buffer
        self._bytes_per_pixel = max(1, int(bits_per_pixel) // 8)
        self._size_line = int(size_line)

    def close(self) -> None:
        """画像とウィンドウを破棄し、メインループを抜ける。"""
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
        except Exception as error:  # noqa: BLE001 - never die while closing
            print(f"Warning: MiniLibX cleanup failed: {error}",
                  file=sys.stderr)
        self.running = False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def build_rows(self) -> List[bytes]:
        """迷路を、キャンバス 1 行につき 1 本のピクセル列として描く。

        Returns:
            ``canvas_rows`` 個のバイト列。それぞれ ``image_width`` 個の
            ピクセルを持ち、そのまま MiniLibX の画像に転写できる。
        """
        canvas = Canvas(self.session.generator)
        canvas.paint_pattern()
        if self.session.show_path:
            canvas.paint_path(self.session.generator.solution)
        canvas.paint_endpoints()
        palette = self._palette()
        cache = {
            token: self._pixel_bytes(colour) * self.scale
            for token, colour in palette.items()
        }
        return [
            b"".join(cache[token] for token in row) for row in canvas.cells
        ]

    def draw(self) -> None:
        """迷路を描き直し、ウィンドウへ転送する。"""
        rows = self.build_rows()
        stride = self._size_line or self.image_width * self._bytes_per_pixel
        for canvas_y, packed in enumerate(rows):
            top = canvas_y * self.scale
            for repeat in range(self.scale):
                start = (top + repeat) * stride
                self._buffer[start:start + len(packed)] = packed
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
        )
        self._draw_footer()

    def _draw_footer(self) -> None:
        """迷路の下にヘルプ行と迷路の統計情報を書く。"""
        white = 0xFFFFFF
        grey = 0x9AA0A6
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win_ptr, 8, self.image_height + 10,
            white, _HELP,
        )
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win_ptr, 8, self.image_height + 22,
            grey, self.session.status(),
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_key(self, keycode: int, param: Any = None) -> None:
        """キー押下を処理する。

        Args:
            keycode: MiniLibX が通知する X11 のキーシム。
            param: ``mlx_key_hook`` に渡した利用者ポインタ。未使用。

        Note:
            これは C のコールバックとして呼ばれる。ここから例外が抜ける
            と ctypes に握り潰されてしまうため、すべて捕まえて報告する。
        """
        try:
            self._dispatch(keycode)
        except Exception as error:  # noqa: BLE001 - keep the window alive
            print(f"Error: {error}", file=sys.stderr)

    def _dispatch(self, keycode: int) -> None:
        """``keycode`` に割り当てられた動作を実行し、描き直す。"""
        session = self.session
        if keycode in (KEY_QUIT, KEY_Q, KEY_ESCAPE):
            self.close()
            return
        if keycode == KEY_REGENERATE:
            try:
                session.regenerate()
            except MazeError as error:
                print(f"Error: {error}", file=sys.stderr)
                return
        elif keycode == KEY_PATH:
            session.toggle_path()
        elif keycode == KEY_COLOURS:
            session.next_theme()
        elif keycode == KEY_PATTERN:
            session.toggle_pattern_colour()
        elif keycode == KEY_SAVE:
            session.save()
            return
        else:
            return
        self.draw()

    def on_close(self, param: Any = None) -> None:
        """ウィンドウの閉じるボタンの押下を処理する。"""
        self.close()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """ウィンドウを開いて迷路を描き、終了されるまでループする。

        Raises:
            MlxUnavailable: ウィンドウを開けない場合。
        """
        self.open()
        print(f"MiniLibX window -- {_HELP}")
        self.draw()
        self.mlx.mlx_key_hook(self.win_ptr, self.on_key, None)
        self.mlx.mlx_hook(
            self.win_ptr,
            _DESTROY_NOTIFY,
            _STRUCTURE_NOTIFY_MASK,
            self.on_close,
            None,
        )
        self.running = True
        try:
            self.mlx.mlx_loop(self.mlx_ptr)
        except KeyboardInterrupt:
            self.close()
        finally:
            self.running = False


def show_in_window(
    session: Session,
    mlx_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """``session`` を MiniLibX のウィンドウに表示する。

    Args:
        session: 迷路と表示オプションを保持するセッション。
        mlx_factory: MiniLibX のインスタンスを返す呼び出し可能
            オブジェクト。テスト用。

    Raises:
        MlxUnavailable: MiniLibX を使えない場合。
    """
    MlxViewer(session, mlx_factory=mlx_factory).run()
