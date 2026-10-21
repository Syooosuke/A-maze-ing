"""MiniLibX を使えるかの判定と、ウィンドウの大きさの決め方。

mlx パッケージ（subject に mlx-2.2.tgz として同梱）は C の MiniLibX を
ctypes で包んだもので、本プロジェクトの必須の依存ではない。使えない
ときは MlxUnavailable を送出し、呼び出し側が端末表示に切り替える。
"""

from __future__ import annotations

from typing import Any, Optional

# 迷路の下に、ヘルプと要約の 2 行を書くための余白（ピクセル）。
FOOTER_HEIGHT = 26

# キャンバスの 1 マスを何ピクセル四方で描くか。
DEFAULT_SCALE = 8
MIN_SCALE = 2
MAX_SCALE = 16


class MlxUnavailable(Exception):
    """この環境では MiniLibX を使えないときに送出する。"""


def load_mlx() -> Any:
    """mlx パッケージの Mlx クラスを読み込んで返す。

    Raises:
        MlxUnavailable: パッケージか、その共有ライブラリが見つからない場合。
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


def choose_scale(
    canvas_cols: int, canvas_rows: int, screen_width: int,
    screen_height: int, wanted: Optional[int] = None,
) -> int:
    """1 マスを何ピクセルで描くかを決める。

    wanted が指定されていればそれを使う。なければ、迷路全体が画面に
    収まるいちばん大きな値を MIN_SCALE〜MAX_SCALE の範囲で選ぶ。画面の
    大きさが分からない（0 が渡された）ときは DEFAULT_SCALE。
    """
    if wanted is not None:
        return max(1, wanted)
    if not screen_width or not screen_height:
        return DEFAULT_SCALE
    # 画面の端やタイトルバーのぶん、少し余裕を残す。
    usable_width = screen_width - 40
    usable_height = screen_height - FOOTER_HEIGHT - 80
    scale = min(usable_width // canvas_cols, usable_height // canvas_rows)
    return max(MIN_SCALE, min(MAX_SCALE, scale))
