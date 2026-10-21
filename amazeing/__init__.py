"""A-Maze-ing のアプリケーション部分（mazegen を使う側）。

再利用できる迷路生成は mazegen パッケージにあり、ここにはコマンドライン
プログラムだけが使う部分を置く。

    config/    設定ファイルの読み込みと検証
    output.py  出力ファイルの書き出し
    display/   端末への表示と対話メニュー
    minilibx/  MiniLibX のウィンドウ（任意機能）
"""
