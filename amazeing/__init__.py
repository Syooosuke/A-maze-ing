"""A-Maze-ing のアプリケーション部分（mazegen を使う側）。

再利用できる迷路生成は mazegen パッケージにあり、ここにはコマンドライン
プログラムだけが使う部分を置く。

    config, config_reader, config_values   設定ファイルの読み込みと検証
    output                                 出力ファイルの書き出し
    canvas, themes, render                 端末への描画
    session, menu                          表示の状態と対話メニュー
    mlxview, mlx_window, mlx_colours       MiniLibX のウィンドウ（任意機能）
"""
