"""A-Maze-ing プロジェクトのアプリケーション層。

再利用可能な迷路生成ロジックは独立した :mod:`mazegen` モジュールにある。
このパッケージが持つのはコマンドラインプログラム固有の部分だけで、設定の
解析、出力ファイルの書き出し、端末描画、対話メニュー、そして任意機能の
MiniLibX ウィンドウが含まれる。
"""

from __future__ import annotations

__all__ = ["config", "mlxview", "output", "render", "ui"]
